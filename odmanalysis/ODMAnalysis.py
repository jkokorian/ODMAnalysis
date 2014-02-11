# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 10:47:31 2013

@author: jkokorian
"""

from __future__ import division
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import chisquare
import os
import ConfigParser
from ProgressReporting import StdOutProgressReporter
import pickle
import copy


def getActuationDirectionAndCycle(dataframe,inplace=True,startDirection='forward',startCycleNumber=1):
    """
    Determines the actuation direction from the actuatorVoltage column of the
    target dataframe.
    
    Parameters
    ----------
    
    df: pandas.DataFrame instance
        The target dataframe. Should have at least a column called 'actuatorVoltage'
    
    inplace: bool (default True)
        Add column 'direction' and 'cycleNumber' to the target dataframe. If false,
        a new dataframe with the same index as the target dataframe and just these
        two columns is returned.
        
    
    Returns
    -------
    
    The target dataframe or a new dataframe depending on the 'inplace' parameter.
    """
    if inplace == True:
        df = dataframe
    else:
        df = pd.DataFrame(index=dataframe.index)
    
    df['direction'] = 'forward'
    df.direction.iloc[0] = startDirection
    df.direction[dataframe.actuatorVoltage.diff() < 0] = 'backward'
    
    s = (df.direction != df.direction.shift(1))
    baseCycleNumbers = pd.Series(np.arange(len(s[s==True])),index=s[s==True].index)
    baseCycleNumbers = baseCycleNumbers //2
    
    df['cycleNumber'] = baseCycleNumbers + startCycleNumber
    df.cycleNumber.fillna(method='pad',inplace=True)
    return df

def readODMData(dataFilePath,progressReporter=StdOutProgressReporter()):
    """
    Reads a data.csv file that has been written by a LabVIEW ODM Measurement and returns
    it as a dataframe. It also determines the cyclenumber and direction.
    
    The data is read from the source file in chunks of 2005 lines. This ensures that also extremely large
    files can be read without memory problems.
    
    Parameters
    ----------

    dataFilePath : string
        Path string to the data.csv file that contains the raw odm data.
    progressReporter : ODMAnalysisGui.ProgressReporter
        The ProgressReporter to use. If None (default) a StdOutProgressReporter is used.

    
    Returns
    -------
    dataframe: pandas.DataFrame,
        A pandas dataframe with the data in data.csv. The index is set to the timestamp. The columns 
        'cycleNumber' and 'direction' have been determined from the 'actuatorVoltage' column.
    """
    
    progressReporter.message('loading data from %s ...' % dataFilePath)
    reader = pd.read_csv(dataFilePath, 
                         sep='\t',names=['timestamp','relativeTime','actuatorVoltage','intensityProfile'],
                         skiprows=1,
                         header=None,
                         parse_dates='timestamp',
                         index_col='timestamp', 
                         chunksize=2005)
    
    def ipStringToArray(ipString):
        ip = ipString.replace('<','[')\
                     .replace('>',']')\
                     .replace(';',',')
        return np.array(eval(ip))
    
    chunks=[]
    for chunk in reader:
        chunk.intensityProfile = chunk.intensityProfile.map(ipStringToArray)
        chunks.append(chunk)
        print "%s - %s" % (chunk.index.min(),chunk.index.max())
    
    df = pd.concat(chunks)
    
    df = df[df.intensityProfile.map(len) != 0]
    
    getActuationDirectionAndCycle(df)

    progressReporter.done()
    
    return df


def readAnalysisData(dataFilePath):
    """
    Reads the csv-file that was produced by the FitRawODMData script back into a DataFrame.
    
    Parameters
    ----------
    
    dataFilePath : string
        Path to the csv file, usually  odmanalysis.csv
        
    
    Returns
    -------
    
    dataframe: pandas.DataFrame
        A pandas dataframe that has the data from the analysis csv file. The index is
        set to 'timestamp'.
    """

    df = pd.read_csv(dataFilePath,index_col='timestamp',parse_dates='timestamp')
    return df


def readCurveFitSettings(fitSettingsPcl):
    """
    Reads pickled curveFitSettings from the target pickle file.
    
    Parameters
    ----------
    
    fitSettingsPcl : string
        Path to the target pickle file (usually fitSettings.pcl)
        
        
    Returns
    -------
    
    settingDict: dictionary
        A dictionary with keys 'movingPeakFitSettings' and 'referencePeakFitSettings' that contain
        the fit settings for the moving peak and reference peak respectively.
    """

    with file(fitSettingsPcl,'r') as f:    
        ffDict = pickle.load(f)
    
    return ffDict


def readCurveFitResults(fitResultsPcl):
    """
    Reads pickled CurveFitResults from the target pickle file back into a dataframe.
    
    Parameters
    ----------
    
    fitResultsPcl: string
        Path to the target pickle file (usually fitResults.pcl)
        
    Returns
    -------
    
    dataframe: pandas.DataFrame
        A dataframe that contains the CurveFitResult objects for each analyzed intensity profile.
        The index of the dataframe is equal to the 'timestamp' column of the corresponding 'odmanalysis.csv' file.
    """
    
    df = pd.DataFrame.load(fitResultsPcl)
    return df


class CurveFitSettings(object):
    def __init__(self):
        self.configFile = None
        self.pxToNm = 1
        self.xkcd = False
        self.numberOfProfiles = 10
        self.defaultFitFunction = ""
        self.hozontalBinning = 1
    
    @classmethod
    def loadFromFile(cls,filename):
        cp = ConfigParser.SafeConfigParser()
        configFile = os.path.abspath(filename)  
        cp.read(configFile)
        
        s = CurveFitSettings()
        s.configFile = configFile
        
        s.pxToNm = cp.getfloat('PostProcessing','resolution')
        s.xkcd = cp.getboolean('PostProcessing','xkcd')
        s.defaultFitFunction = cp.get('Analysis','defaultFitFunction')
        
        return s
    
    @classmethod
    def loadFromFileOrCreateDefault(cls,filename,prototype=None):
        if prototype and not isinstance(prototype,CurveFitSettings):
            raise TypeError("prototype must be an instance of CurveFitSettings or None")
        
        if (os.path.isfile(filename)):
            return CurveFitSettings.loadFromFile(filename)
        else:
            if prototype:
                s = copy.copy(prototype)
            else:
                s = CurveFitSettings()
            
            s.saveToFile(filename)
            return s
    
    
    def saveToFile(self,filename=None):
        
        if (filename):
            self.configFile = os.path.abspath(filename)
            
        cp = ConfigParser.SafeConfigParser()
        configFile = os.path.abspath(filename)
        cp.read(configFile)
        
        if (not cp.has_section('PostProcessing')):
            cp.add_section('PostProcessing')
        if (not cp.has_section('Analysis')):
            cp.add_section('Analysis')
        
        cp.set('PostProcessing','resolution',str(self.pxToNm))
        cp.set('PostProcessing','xkcd',str(self.xkcd))
        cp.set('Analysis','defaultFitFunction',self.defaultFitFunction)
        
        with file(self.configFile,'w') as fp:
            cp.write(fp)


class OpticsSettings(object):
    def __init__(self):
        self.nmPerPx = 1
        self.magnification = 1
        self.configFile = ""
    
    @classmethod
    def loadFromFile(cls,filename):
        print filename
        cp = ConfigParser.SafeConfigParser()
        configFile = os.path.abspath(filename)  
        print configFile
        cp.read(configFile)
        
        s = OpticsSettings()
        s.configFile = configFile
        try:
            s.nmPerPx = cp.getfloat('Optics','NanometersPerPixel')
            s.magnification = cp.getfloat('Optics','NanometersPerPixel')
        except:
            print "settings could not be loaded"
        return s
    
    @classmethod
    def loadFromFileOrCreateDefault(cls,filename):
        if (os.path.isfile(filename)):
            return OpticsSettings.loadFromFile(filename)
        else:
            s = OpticsSettings()
            s.saveToFile(filename)
            return s    
    
    def saveToFile(self,filename=None):
        
        if (filename):
            self.configFile = os.path.abspath(filename)
            
        cp = ConfigParser.SafeConfigParser()
        configFile = os.path.abspath(filename)
        cp.read(configFile)
        
        if (not cp.has_section('Optics')):
            cp.add_section('Optics')
        
        cp.set('Optics','NanometersPerPixel',str(self.nmPerPx))
        
        with file(self.configFile,'w') as fp:
            cp.write(fp)
    
    @classmethod
    def loadFromFileOrCreateDefault(cls,filename):
        if (os.path.isfile(filename)):
            return OpticsSettings.loadFromFile(filename)
        else:
            s = OpticsSettings()
            s.saveToFile(filename)
            return s

class ODAFitSettings(object):
    def __init__(self,fitFunction,estimatorValuesDict):
        self.xminBound = int(round(estimatorValuesDict['minBound'][0]))
        self.xmaxBound = int(round(estimatorValuesDict['maxBound'][0]))
        self.fitFunction = fitFunction
        self.estimatorValuesDict = estimatorValuesDict
    
    def toDict(self):
        return {'fitFunction': self.fitFunction.getName(),
                'xminBound': self.xminBound,
                'xmaxBound': self.xmaxBound,
                'estimatorValues': self.estimatorValuesDict}
    

class CurveFitResult(object):
    def __init__(self):
        self.popt = None
        self.pcov = None
        self.chisquare = None




def calculatePeakDisplacements(intensityProfiles, peakFitSettings, progressReporter = None, pInitial = None, **curveFitKwargs):
    """
    Fits an ODM FitFunction to the target Series of intensity profiles.
    
    Parameters
    ----------
    
    intensityProfiles : pandas.Series of 1D numpy.ndarray
        A series of intensityProfiles that will be curve fit
    peakFitSettings : CurveFitSettings instance
        The curve fit settings to use for curve fitting
    progressReporter : ProgressReporter instance
        The ProgressReporter to use for displaying progress information. 
        A StdOutProgressReporter is used by default.
    curveFitKwargs : Keyword arguments that will be passed to the curve_fit
        function (scipy.optimization).
    
    
    Returns
    -------

    A dataframe with the calculated displacements that has the same index as the input
    intensity profile Series.
    """
    
    if not progressReporter:
        progressReporter = StdOutProgressReporter()
    
    fitFunction = peakFitSettings.fitFunction
    df = pd.DataFrame(index=intensityProfiles.index)
    df['displacement'] = 0.0
    df['curveFitResult'] = CurveFitResult()
    df['chiSquare'] = 0.0
    if pInitial is not None:        
        p0 = pInitial
    else:
        estimatesDict = fitFunction.estimateInitialParameters(intensityProfiles[0], **peakFitSettings.estimatorValuesDict)
        p0 = estimatesDict.values()
        
    xmin = peakFitSettings.xminBound
    xmax = peakFitSettings.xmaxBound
    xdata = np.arange(len(intensityProfiles[0]))[xmin:xmax]
    
    progress = 0.0
    total = len(df.index)
    for i in df.index:
         ydata = intensityProfiles[i][xmin:xmax]
         popt,pcov = curve_fit(fitFunction,\
                  xdata = xdata,\
                  ydata = ydata,\
                  p0 = p0,**curveFitKwargs)
         p0 = popt
        
         curveFitResult = CurveFitResult()         

         curveFitResult.popt = popt
         curveFitResult.pcov = pcov         
         curveFitResult.chisquare = chisquare(ydata,fitFunction(xdata,*popt))[0]
         
         df.curveFitResult[i] = curveFitResult         
         df.displacement[i] = fitFunction.getDisplacement(*popt)         
         df.chiSquare[i] = curveFitResult.chisquare
         
         progress += 1
         progressReporter.progress(progress / total * 100)
    
    progressReporter.done()
    
    return df