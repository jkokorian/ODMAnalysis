# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 13:50:25 2013

@author: jkokorian
"""

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys
import os
import pandas as pd
from Queue import Queue, Full
from threading import Thread
import multiprocessing as mp
import odmanalysis as odm
import odmanalysis.gui as gui
import odmanalysis.fitfunctions as ff


class ChunkReader(object):
    def __init__(self,path):
        self.nlinesRead = 0
        self.path = path
        self.dataframes = []
    
    def read_next(self,*args):
        print "reading"
        with file(self.path,'r') as stream:
            reader = odm.getODMDataReader(stream,chunksize=1000, skipDataRows=self.nlinesRead)
            
            chunks = [chunk for chunk in reader if chunk is not None]
            if len(chunks) > 0:
                df = pd.concat(chunks)
                df = df[df.intensityProfile.map(len) > 0]
        
        self.nlinesRead += len(df.index)
        print "%i new lines read" % len(df.index)
        return df
    

class ChunkWriter(object):
    def __init__(self,outputFile):
        self.outputFile = outputFile
        self.outStream = None
        self.lastDataFrame = None
    
    def writeDataFrame(self,df):
        print "writing"
        
        header = False
        if self.outStream is None:
            if os.path.exists(self.outputFile):
                os.remove(self.outputFile)
            self.outStream = file(self.outputFile,'a')
            header = True
        
        if (self.lastDataFrame is not None):
            tail = self.lastDataFrame.iloc[-2:]
            dfC = pd.concat([tail,df])
            odm.getActuationDirectionAndCycle(dfC,startDirection = tail.direction.iloc[1],startCycleNumber = tail.cycleNumber.iloc[1])
            df = dfC.iloc[2:]
        else:
            odm.getActuationDirectionAndCycle(df)
            
        
        exportColumns = ['relativeTime','cycleNumber','direction','actuatorVoltage','displacement','displacement_mp','chiSquare_mp']
        if ('displacement_ref' in df.columns):
            exportColumns +=['displacement_ref','chiSquare_ref']
        df[exportColumns].to_csv(self.outStream,index_label='timestamp',header=header)
        
        self.lastDataFrame = df
        print "done"



class OMDCsvChunkHandler(FileSystemEventHandler):
    """
    Handler for watchdog filesystem events.
    
    Description
    -----------
    
    This class hosts three consumer/producer threads for the following functions
    
        - producer: reading chunks of data from the input file.
        - consumer-producer: processing chunks of data
        - consumer: writing chunks of data to the output file
        
    When a change is detected on the target input file a flag is raised to the
    'reader' thread to read a chunk of data. This chunk is then passed on to the
    dataProcessing consumer thread where the displacement is detected and stored to an
    output dataframe. This dataframe is passed to the outputwriter consumer thread that
    writes it to the output csv file.
    """    
    
    def __init__(self,inputFile,outputFile):
        self.inputFile = inputFile
        
        self.fileQueue = Queue(1)
        self.rawDataframeQueue = Queue()
        self.processedDataframeQueue = Queue()
        
        self.chunkReader = ChunkReader(inputFile)
        self.dataProcessor = ChunkedODMDataProcessor(os.path.abspath(os.path.split(inputFile)[0]))
        self.chunkWriter = ChunkWriter(outputFile)
        
        self.fileConsumerThread = ReturnActionConsumerThread(self.chunkReader.read_next,self.fileQueue,self.rawDataframeQueue)
        self.odmProcessorThread = ReturnActionConsumerThread(self.dataProcessor.processDataFrame,self.rawDataframeQueue,self.processedDataframeQueue)
        self.outputWriterThread = ReturnActionConsumerThread(self.chunkWriter.writeDataFrame,self.processedDataframeQueue)
        
        
        
    def on_modified(self, event):
        if (event.src_path == self.inputFile):
            try:
                self.fileQueue.put(True,block=False)
            except Full:
                pass
    
    def startPCChain(self):
        self.fileConsumerThread.start()
        self.odmProcessorThread.start()
        self.outputWriterThread.start()
    
    def stopPCChain(self):
        pass
        


class ChunkedODMDataProcessor(object):
    """
    Instances of this class process chunks of raw odm dataframes.
    """
    
    def __init__(self,commonPath):
        """
        TODO: class should not know anything about 'inputFiles', only about chunks of dataframes        
        
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
            globalSettings = odm.CurveFitSettings.loadFromFileOrCreateDefault('./CurveFitScriptSettings.ini')
            settings = odm.CurveFitSettings.loadFromFileOrCreateDefault(self.commonPath + '/odmSettings.ini',prototype=globalSettings)
            gui.getSettingsFromUser(settings)
            self.curveFitSettings = settings
            settings.saveToFile()
        
        if not self.movingPeakFitSettings:
            q = mp.Queue() #it is nescessary to host all gui elements in their own process, because the cannot be spawned from another thread than the main one.
            p = mp.Process(target=_getPeakFitSettingsFromUser, args=(q,df,settings))
            p.start()
            settingsDict = q.get()
            p.join()
            self.movingPeakFitSettings = settingsDict['movingPeakFitSettings']
            self.referencePeakFitSettings = settingsDict['referencePeakFitSettings']
           
        df_movingPeak = odm.calculatePeakDisplacements(df.intensityProfile, self.movingPeakFitSettings, pInitial = self.popt_mp_previous, factor=100,maxfev=20000)
        
        df_movingPeak.rename(columns = lambda columnName: columnName + "_mp",inplace=True)
        df = df.join(df_movingPeak)
        self.popt_mp_previous = df.curveFitResult_mp[-1].popt
        
        if (self.referencePeakFitSettings is not None):
            df_referencePeak = odm.calculatePeakDisplacements(df.intensityProfile, self.referencePeakFitSettings, pInitial = self.popt_ref_previous, factor=100,maxfev=20000)
            df_referencePeak.rename(columns = lambda columnName: columnName + "_ref",inplace=True)
            df = df.join(df_referencePeak)
            self.popt_ref_previous = df.curveFitResult_ref[-1].popt
            df['displacement'] = df.displacement_mp - df.displacement_ref
        else:
            df['displacement'] = df.displacement_mp
        
        return df
            


class StartActionConsumerThread(Thread):
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


class ReturnActionConsumerThread(Thread):
    """
    Monitors an inputQueue for data which is entered as a function argument to 'action',
    the return data is queued into the outputQueue.
    """    
    
    def __init__(self,action,inputQueue,outputQueue=None):
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
        """
        
        super(ReturnActionConsumerThread,self).__init__()
        
        self.action = action
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        print "consumer initialized"
        
    def run(self):
        print "consumer started"
        while True:
            arg = self.inputQueue.get()
            self.inputQueue.task_done()
            value = self.action(arg)
            if (self.outputQueue is not None): 
                self.outputQueue.put(value)
            

def _getPeakFitSettingsFromUser(q,df,settings):
    """
    Helper method to be able to start the gui from another thread than the main one.
    Use it by starting a Process (multiprocessing module) that executes this function.
    """
    
    movingPeakFitFunction = ff.createFitFunction(settings.defaultFitFunction)
    movingPeakFitSettings = gui.getPeakFitSettingsFromUser(df.intensityProfile.iloc[0],movingPeakFitFunction,
                                                       estimatorPromptPrefix="Moving peak:",
                                                       windowTitle="Moving Peak estimates")
    
    try:
        referencePeakFitFunction = ff.createFitFunction(settings.defaultFitFunction)
        referencePeakFitSettings = gui.getPeakFitSettingsFromUser(df.intensityProfile.iloc[1],referencePeakFitFunction,
                                                                  estimatorPromptPrefix="Reference peak:",
                                                                  windowTitle="Reference Peak estimates")
        
        
    except: #exception occurs if user cancels the 'dialog'
        referencePeakFitFunction = None        
        referencePeakFitSettings = None
        
    q.put({'movingPeakFitSettings': movingPeakFitSettings,
           'referencePeakFitSettings': referencePeakFitSettings})


def main():
    if (len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1])):
        filename = sys.argv[1]
    else:
        filename = gui.get_path("*.csv",defaultFile="data.csv")
    
    commonPath = os.path.abspath(os.path.split(filename)[0])
    outputFile = os.path.join(commonPath, "odmanalysis.csv")
    
    print "Now watching %s for changes" % filename
    handler = OMDCsvChunkHandler(filename,outputFile)
    observer = Observer()
    observer.schedule(handler, path=commonPath, recursive=False)
    handler.startPCChain()
    observer.start()

    try:
        while True:
            time.sleep(1)
                
    except (KeyboardInterrupt, SystemExit):
        print "Stopping..."
        observer.stop()
        time.sleep(1)
    observer.join()
    

if __name__ == "__main__":
    main()