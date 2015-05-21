from PyQt4 import QtCore as q
from PyQt4 import QtGui as qt
import pandas as pd
import numpy as np
import odmanalysis as odm
from odmanalysis.odmstudio.odmstudio_framework import RegisterSourceReader
import cv2
   
    
class DataSource(q.QObject):
    
    @classmethod
    def createDefaultSourceDataFrame(cls):
        return pd.DataFrame(data={"intensityProfile": []})

    @classmethod
    def createDefaultResultsDataFrame(cls):
        return pd.DataFrame()

    sourceDataChanged = q.pyqtSignal(pd.DataFrame)
    resultDataChanged = q.pyqtSignal(pd.DataFrame)
    sourcePathChanged = q.pyqtSignal(str)

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
        self.__currentIloc = iloc

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
    
    @property
    def tracker(self):
        return self._tracker

    @property
    def dataSource(self):
        return self._dataSource

    def __init__(self,name,shortName,dataSource):
        super(TrackableFeature,self).__init__()
        
        self.name = name
        self.shortName = shortName
        self.lowerLimit = 0        
        self.upperLimit = 0        
        self._tracker = FeatureTracker()
        assert isinstance(dataSource,DataSource)
        self._dataSource = dataSource
        
    
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

    

    def locateInCurrent(self):
        """
        Searches the currently selected intensity profile of the datasource within the limits for the feature using the tracker
        """
        position = self.tracker.findNextPosition(self.dataSource.currentIntensityProfile)
        self._trackedPositions[self.dataSource.currentIndexLocation] = position
        self._dataSource

    def locateAll(self):
        """
        Searches all the intensityProfiles in the dataSource for the feature
        """
        pass
    
     
    def setLowerLimit(self,value):
        self.lowerLimit = value

    def setUpperLimit(self,value):
        self.upperLimit = value
        


        

        
    