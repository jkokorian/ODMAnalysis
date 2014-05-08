"""
    Copyright (C) 2014 Delft University of Technology, The Netherlands

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Created on Sun Dec 15 13:50:25 2013

@author: jkokorian
"""

import os as _os
import pandas as _pd
from threading import Thread as _Thread
import multiprocessing as _mp
import odmanalysis as _odm
import odmanalysis.gui as _gui
import odmanalysis.fitfunctions as _ff
from odmanalysis.ProgressReporting import BasicProgressReporter as _BasicProgressReporter


class ChunkReader(object):
    """
    Reads the target raw ODM data file into a dataframe. For subsequent calls of
    'read', the file is reopened every time and reading continues where the last read ended.
    """
    def __init__(self,path):
        self.nlinesRead = 0
        self.path = path
        self.dataframes = []
    
    @_BasicProgressReporter(entryMessage="Reading...",exitMessage="")
    def read_next(self,progressReporter=None):
        df = None
        
        with file(self.path,'r') as stream:
            reader = _odm.getODMDataReader(stream,chunksize=1000, skipDataRows=self.nlinesRead)
            
            chunks = [chunk for chunk in reader if chunk is not None]
            if len(chunks) > 0:
                df = _pd.concat(chunks)
                df = df[df.intensityProfile.map(len) > 0]
        
        if (df is not None):
            self.nlinesRead += len(df.index)
            if (progressReporter):
                progressReporter.message("%i new lines read" % len(df.index))
        
        return df
        
    

class ChunkWriter(object):
    """
    Appends an ODM analysis dataframe (chunk) to a csv file.
    """
    def __init__(self,outputFile):
        self.outputFile = outputFile
        self.outStream = None
    
    @_BasicProgressReporter(entryMessage="Writing...",exitMessage="Done")
    def writeDataFrame(self,df):
        header = False
        if self.outStream is None:
            if _os.path.exists(self.outputFile):
                _os.remove(self.outputFile)
            self.outStream = file(self.outputFile,'a')
            header = True
        
        exportColumns = ['relativeTime','cycleNumber','direction','actuatorVoltage','displacement','displacement_mp','chiSquare_mp']
        if ('displacement_ref' in df.columns):
            exportColumns +=['displacement_ref','chiSquare_ref']
        df[exportColumns].to_csv(self.outStream,index_label='timestamp',header=header)
        
class ChunkedODMDataProcessor(object):
    """
    Instances of this class process chunks of raw odm dataframes.
    """
    
    def __init__(self,commonPath):
        """
        Parameters
        ----------
        
        inputFile: string
            path to the file that is being processed
        """
        self.commonPath = commonPath
        self.curveFitSettings = None
        self.movingPeakFitSettings = None
        self.referencePeakFitSettings = None
        self.popt_mp_previous = None
        self.popt_ref_previous = None
        self.lastDataFrame = None
        
    
    def processDataFrame(self,df):
        """
        Processes a dataframe of raw odm data and analyzes the displacement. If this is the first dataframe
        that is being processed, the gui will show to ask the user for fit-function details.
        
        For subsequent calls to this method, the last fit-result of the previous dataframe
        is used as the initial parameters for the fit in the current dataframe.
        
        Parameters
        ----------
        
        df: pandas.DataFrame
            ODM dataframe that contains the raw ODM data
        
        
        """
        if df is None:
            return None
        
        print "processing %s - %s" % (df.index.min(),df.index.max())
        
        if not self.curveFitSettings:
            globalSettings = _odm.CurveFitSettings.loadFromFileOrCreateDefault('./CurveFitScriptSettings.ini')
            settings = _odm.CurveFitSettings.loadFromFileOrCreateDefault(self.commonPath + '/odmSettings.ini',prototype=globalSettings)
            _gui.getSettingsFromUser(settings)
            self.curveFitSettings = settings
            settings.saveToFile()
        
        if not self.movingPeakFitSettings:
            q = _mp.Queue() #it is nescessary to host all gui elements in their own process, because the cannot be spawned from another thread than the main one.
            p = _mp.Process(target=_getPeakFitSettingsFromUser, args=(q,df,settings))
            p.start()
            settingsDict = q.get()
            p.join()
            self.movingPeakFitSettings = settingsDict['movingPeakFitSettings']
            self.referencePeakFitSettings = settingsDict['referencePeakFitSettings']
           
        df_movingPeak = _odm.calculatePeakDisplacements(df.intensityProfile, self.movingPeakFitSettings, pInitial = self.popt_mp_previous, factor=100,maxfev=20000)
        
        df_movingPeak.rename(columns = lambda columnName: columnName + "_mp",inplace=True)
        df = df.join(df_movingPeak)
        self.popt_mp_previous = df.curveFitResult_mp[-1].popt
        
        if (self.referencePeakFitSettings is not None):
            df_referencePeak = _odm.calculatePeakDisplacements(df.intensityProfile, self.referencePeakFitSettings, pInitial = self.popt_ref_previous, factor=100,maxfev=20000)
            df_referencePeak.rename(columns = lambda columnName: columnName + "_ref",inplace=True)
            df = df.join(df_referencePeak)
            self.popt_ref_previous = df.curveFitResult_ref[-1].popt
            df['displacement'] = df.displacement_mp - df.displacement_ref
        else:
            df['displacement'] = df.displacement_mp
        
        if (self.lastDataFrame is not None):
            tail = self.lastDataFrame.iloc[-2:]
            dfC = _pd.concat([tail,df])
            _odm.getActuationDirectionAndCycle(dfC,startDirection = tail.direction.iloc[1],startCycleNumber = tail.cycleNumber.iloc[1])
            df = dfC.iloc[2:]
        else:
            _odm.getActuationDirectionAndCycle(df)
        
        self.lastDataFrame = df
        
        return df
            


class StartActionConsumerThread(_Thread):
    """
    Monitors an inputqueue for callable items. Each dequeued item is executed.
    No return values are captured.
    """

    def __init__(self,queue):
        super(StartActionConsumerThread,self).__init__()
        self.queue = queue
        
    def run(self):
        while True:
            action = self.queue.get()
            self.queue.task_done()
            action()


class ReturnActionConsumerThread(_Thread):
    """
    Monitors an inputQueue for data which is entered as a function argument to 'action',
    the return data is queued into the outputQueue.
    """    
    
    def __init__(self,action,inputQueue,outputQueue=None,discardNoneValues=True):
        """
        Parameters
        ----------
        
        action: callable with a single argument.
            The action that is called on each element that is dequeued from the
            inputQueue.
        
        inputQueue: Queue instance
            The consumer queue.
            
        outputQueue: Queue instance
            The producer queue where return values from 'action' are written to. 
            If None, return values are discarded.
        
        discardNoneValues: boolean
            Values of None read from the inputQueue are discarded without passing
            them to the action function. None values that are returned from the
            action function are also discarded without passing them to the output
            queue.
        """
        
        super(ReturnActionConsumerThread,self).__init__()
        
        self.action = action
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.discardNoneValues = discardNoneValues
        print "consumer initialized"
        
    def run(self):
        print "consumer started"
        while True:
            arg = self.inputQueue.get()
            self.inputQueue.task_done()
            if isinstance(arg,tuple):
                value = self.action(*arg)
            else:
                value = self.action(arg)
            if (self.outputQueue is not None):
                if (value is None and self.discardNoneValues):
                    pass
                else:
                    self.outputQueue.put(value)
            

def _getPeakFitSettingsFromUser(q,df,settings):
    """
    Helper method to be able to start the gui from another thread than the main one.
    Use it by starting a Process (multiprocessing module) that executes this function.
    """
    
    movingPeakFitFunction = _ff.createFitFunction(settings.defaultFitFunction)
    movingPeakFitSettings = _gui.getPeakFitSettingsFromUser(df.intensityProfile.iloc[0],movingPeakFitFunction,
                                                       estimatorPromptPrefix="Moving peak:",
                                                       windowTitle="Moving Peak estimates")
    
    try:
        referencePeakFitFunction = _ff.createFitFunction(settings.defaultFitFunction)
        referencePeakFitSettings = _gui.getPeakFitSettingsFromUser(df.intensityProfile.iloc[1],referencePeakFitFunction,
                                                                  estimatorPromptPrefix="Reference peak:",
                                                                  windowTitle="Reference Peak estimates")
        
        
    except: #exception occurs if user cancels the 'dialog'
        referencePeakFitFunction = None        
        referencePeakFitSettings = None
        
    q.put({'movingPeakFitSettings': movingPeakFitSettings,
           'referencePeakFitSettings': referencePeakFitSettings})

