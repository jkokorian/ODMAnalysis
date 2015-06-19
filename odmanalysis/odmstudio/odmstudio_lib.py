from PyQt4 import QtCore as q
from PyQt4 import QtGui as qt
import pandas as pd
import numpy as np
import odmanalysis as odm
from odmanalysis.odmstudio.odmstudio_framework import RegisterSourceReader
import cv2
import time
    
class DataSource(q.QObject):
    
    @classmethod
    def createDefaultSourceDataFrame(cls):
        return pd.DataFrame(data={"intensityProfile": []})

    @classmethod
    def createDefaultResultsDataFrame(cls):
        return pd.DataFrame()

    sourceDataChanged = q.pyqtSignal(pd.DataFrame)
    resultDataChanged = q.pyqtSignal(pd.DataFrame)
    resultDataCleared = q.pyqtSignal()
    sourcePathChanged = q.pyqtSignal(str)
    currentIndexLocationChanged = q.pyqtSignal(int)


    @property
    def sourcePath(self):
        return self.__sourcePath

    @property
    def sourceDataFrame(self):
        return self.__sourceDataFrame
    
    @property
    def resultsDataFrame(self):
        return pd.DataFrame(data=self.__resultsDataFrame)

    @property
    def intensityProfiles(self):
        return self.sourceDataFrame['intensityProfile']

    @property
    def currentIndexLocation(self):
        return self.__currentIloc
    
    @property
    def currentIntensityProfile(self):
        return self.intensityProfiles.iloc[self.currentIndexLocation]
    
    @property
    def sourceLength(self):
        return len(self.sourceDataFrame)

    @property
    def resultsLength(self):
        return len(self.resultsDataFrame)

    @property
    def sourceIsEmpty(self):
        return self.sourceLength == 0

    @property
    def resultsIsEmpty(self):
        return self.resultsLength == 0

    @property
    def independentVariableNames(self):
        return [columnName for columnName in df.columns if df[columnName].dtype == 'float' or df[columnName].dtype == 'int']
    
    def __init__(self):
        q.QObject.__init__(self)
        self.__sourceDataFrame = DataSource.createDefaultSourceDataFrame()
        self.__resultsDataFrame = DataSource.createDefaultResultsDataFrame()
        self.__resultArrays = {}
        self.__currentIloc = 0
        self.__sourcePath = ""


    def setCurrentIndexLocation(self,iloc):
        if self.__currentIloc != iloc:
            self.__currentIloc = iloc
            self.currentIndexLocationChanged.emit(iloc)

    def setSourceDataFrame(self,dataframe):
        self.__sourceDataFrame = dataframe
        self.__resultsDataFrame = pd.DataFrame(index=dataframe.index)
        self.sourceDataChanged.emit(dataframe)
        self.resultDataChanged.emit(self.__resultsDataFrame)

    def setSourcePath(self,path):
        self.__sourcePath = path
        self.sourcePathChanged.emit(path)

    def clear(self):
        self.setSourceDataFrame(DataSource.createDefaultSourceDataFrame())
        self.setSourcePath("")

    def clearResults(self):
        self.__resultArrays = {}
        self.__resultsDataFrame = DataSource.createDefaultResultsDataFrame()
        self.resultDataCleared.emit()

    def createResultColumn(self,name,dtype='float'):
        if not self.__resultArrays.has_key(name):
            a = np.empty_like(self.resultsDataFrame.index,dtype=dtype)
            a.fill(None)
            self.__resultArrays[name] = a
            self.resultsDataFrame[name] = pd.Series(data=a,index=self.resultsDataFrame.index)
        
        else:
            raise NameError("a result column with this name already exists")
    
    def getOrCreateResultColumn(self,name,dtype='float'):
        if not self.__resultArrays.has_key(name):
            self.createResultColumn(name,dtype=dtype)
            
        return self.__resultArrays[name]

    def refreshResults(self):
        """
        Emits the resultsDataChanged signal.
        """
        self.resultDataChanged.emit(self.resultsDataFrame)

            

        
        
        
            

class SourceReader(q.QObject):
    
    
    statusMessageChanged = q.pyqtSignal(str)
    progressChanged = q.pyqtSignal(int)
    
    @property
    def dataSource(self):
        return self.__dataSource

    @property
    def statusMessage(self):
        return self._statusMessage
        
    @property
    def currentPath(self):
        return self._currentPath

    @property
    def progress(self):
        return self._progress

    
    def __init__(self,dataSource):
        """
        Parameters
        ----------

        dataSource: DataSource
        """
        super(SourceReader,self).__init__()
        self.data = None
        self._statusMessage = "idle"
        self._progress = None
        self._currentFile = None

        assert isinstance(dataSource,DataSource)
        self.__dataSource = dataSource
        
    def _setStatusMessage(self,message):
        self._statusMessage = message
        self.statusMessageChanged.emit(message)

    def _setProgress(self,progress):
        self._progress = progress
        self.progressChanged.emit(progress)

        
    def _emitDataChanged(self):
        self.dataChanged.emit(self.data)

    def read(self,path):
        """
        Read data from path synchronously.

        Override this method to implement the logic for reading from the path. Make sure to call this super method before doing anything else.
        """
        
        self.__dataSource.clear()
        
        

    def _setCurrentPath(self,path):
        self._currentPath = path
        self.sourceChanged.emit(str(path))   


    def readAsync(self,path):
        """
        Read data from path asynchronously.

        Returns
        -------

        A QThread object for the asynchronous reading operation
        """
        
        
        that = self
        class DataLoaderThread(q.QThread):
            def run(self):
                that.read(path)



        thread = DataLoaderThread()
        thread.start()
        
        
        return thread

       


class FeatureTracker(q.QObject):

    @classmethod
    def getDisplayName(cls):
        return str(cls)

    @property
    def rangeSlice(self):
        return slice(self.xmin,self.xmax)
    
    def __init__(self):
        q.QObject.__init__(self)
        self.xmin = None
        self.xmax = None
    
    def findNextPosition(self,intensityProfile):
        raise NotImplemented("Implement this method in child class")

    def initialize(self,intensityProfile):
        pass

    def setXmin(self,value):
        self.xmin = value
    
    def setXmax(self,value):
        self.xmax = value


    



class TrackableFeature(q.QObject):
    
    regionChanged = q.pyqtSignal(tuple)


    @property
    def tracker(self):
        return self._tracker

    @property
    def dataSource(self):
        return self._dataSource
    
    @property
    def lowerLimit(self):
        return self.region[0]

    @property
    def upperLimit(self):
        return self.region[1]


    def __init__(self,name,shortName,dataSource):
        super(TrackableFeature,self).__init__()
        
        self.name = name
        self.shortName = shortName
        self.region = [0,0]   
        self._tracker = FeatureTracker()
        assert isinstance(dataSource,DataSource)
        self._dataSource = dataSource
        self._trackedPositions = np.array([])

        #connect signals and slots
        self._dataSource.resultDataCleared.connect(self.clearTrackedPositions)

    def setTracker(self,tracker):
        self._tracker = tracker
    

    def setDataSource(self,dataSource):
        self._sourceData = dataSource
    

    def initializeTracker(self):
        """
        Initializes the tracker on the currently selected intensityProfile of the dataSource
        """

        self.tracker.initialize(self.dataSource.currentIntensityProfile)
        self._trackedPositions = self.dataSource.getOrCreateResultColumn("displacement_%s" % self.shortName)
        
    def clearTrackedPositions(self):
        self._trackedPositions = None

    def locateAtIndexLocation(self, i, refreshDataSource=True):
        """
        Searches the the i'th intensity profile of the datasource within the limits for the feature using the tracker
        """
        position = self.tracker.findNextPosition(self.dataSource.intensityProfiles.iloc[i])
        self._trackedPositions[i] = position
        if refreshDataSource == True:
            self.dataSource.refreshResults()

        return position

    def locateInCurrent(self, refreshDataSource=True):
        """
        Searches the currently selected intensity profile of the datasource within the limits for the feature using the tracker
        """
        return self.locateAtIndexLocation(self.dataSource.currentIndexLocation)

    def locateAll(self, refreshDataSource=True):
        """
        Searches all the intensityProfiles in the dataSource for the feature
        """

        updateInterval = 10

        for i in range(0, self.dataSource.sourceLength):
            self.locateAtIndexLocation(i, refreshDataSource = False)
            if i%10 == 0:
                self.dataSource.setCurrentIndexLocation(i)
                self.dataSource.refreshResults()
        
        if refreshDataSource == True:
            self.dataSource.refreshResults()
        

    
    def locateAllAsync(self):

        that = self

        class AnalyzerThread(q.QThread):
            def run(self):
                that.locateAll()

        self.analyzerThread = AnalyzerThread()
        self.analyzerThread.start()
        return self.analyzerThread


    def getRegion(self):
        return self.region[:]
     
    def setRegion(self,region):
        self.region[0] = region[0]
        self.region[1] = region[1]
        self._tracker.setXmin(region[0])
        self._tracker.setXmax(region[1])
        self.regionChanged.emit(region)

    def getLowerLimit(self):
        return self.region[0]

    def setLowerLimit(self,value):
        if value != self.region[0]:
            self.region[0] = value
            self.regionChanged.emit(tuple(self.region))

    def getUpperLimit(self):
        return self.region[1]

    def setUpperLimit(self,value):
        if value != self.region[1]:
            self.region[1] = value
            self.regionChanged.emit(tuple(self.region))
        
    
class TrackableFeaturePair(q.QObject):

    @property
    def dataSource(self):
        return self._dataSource

    def __init__(self, dataSource, parent=None):
        super(TrackableFeaturePair, self).__init__(parent=None)

        assert isinstance(dataSource,DataSource)
        self._dataSource = dataSource
        
        self.movingFeature = TrackableFeature("moving","mp", dataSource)
        self.referenceFeature = TrackableFeature("reference", "ref", dataSource)

        #connect signals and slots
        self._dataSource.resultDataCleared.connect(self.clearTrackedPositions)

    def initializeTrackers(self):
        """
        Initializes the trackers for the moving feature and the reference feature and adds a differtial result array to the datasource.
        """
        self.referenceFeature.initializeTracker();
        self.movingFeature.initializeTracker();

        self._differentialResultColumn = self._dataSource.getOrCreateResultColumn("displacement_diff")

    def clearTrackedPositions(self):
        self._differentialResultColumn = None

    def locateAtIndexLocation(self, i, refreshDataSource = True):
        movingPeakPosition = self.movingFeature.locateAtIndexLocation(i,refreshDataSource=False)
        referencePeakPosition = self.referenceFeature.locateAtIndexLocation(i,refreshDataSource=False)
        differentialPosition = movingPeakPosition - referencePeakPosition
        self._differentialResultColumn[i] = differentialPosition
        
        if refreshDataSource == True:
            self.dataSource.refreshResults()

    
    def locateInCurrent(self):
        self.locateAtIndexLocation(self.dataSource.currentIndexLocation)
        
    def locateAll(self, refreshDataSource=True):
        """
        Searches all the intensityProfiles in the dataSource for the feature
        """

        updateInterval = 10

        for i in range(0, self.dataSource.sourceLength):
            self.locateAtIndexLocation(i, refreshDataSource = False)
            if i%10 == 0:
                self.dataSource.setCurrentIndexLocation(i)
                self.dataSource.refreshResults()
        
        if refreshDataSource == True:
            self.dataSource.refreshResults()
        

    def locateAllAsync(self):
        that = self

        class AnalyzerThread(q.QThread):
            def run(self):
                that.locateAll()

        self.analyzerThread = AnalyzerThread()
        self.analyzerThread.start()
        return self.analyzerThread
        


    
    