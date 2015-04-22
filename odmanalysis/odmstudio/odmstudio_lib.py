from PyQt4 import QtCore as q
from PyQt4 import QtGui as qt
import pandas as pd
import numpy as np
import odmanalysis as odm


class SourceReader(q.QObject):
    
    dataChanged = q.pyqtSignal(pd.DataFrame)
    sourceChanged = q.pyqtSignal(str)

    
    def __init__(self):
        super(SourceReader,self).__init__()
        self.data = None
        
    def _emitDataChanged(self):
        self.dataChanged.emit(self.data)
        

class CsvReader(SourceReader):
    
    statusMessageChanged = q.pyqtSignal(str)
    progressChanged = q.pyqtSignal(int)

    def __init__(self):
        SourceReader.__init__(self)
        self._statusMessage = "idle"
        self._progress = None
        self._currentFile = None
        
    @property
    def statusMessage(self):
        return self._statusMessage
        
    
    def _setStatusMessage(self,message):
        self._statusMessage = message
        self.statusMessageChanged.emit(message)

    @property
    def progress(self):
        return self._progress

    def _setProgress(self,progress):
        self._progress = progress
        self.progressChanged.emit(progress)


    def loadDataFromFile(self,filename):
        self.data = None
        self._setStatusMessage("reading...")
        reader = odm.getODMDataReader(filename,chunksize=500)
        
        lineCount = float(sum(1 for line in open(filename)))
        chunks = []
        linesRead = 1
        for chunk in reader:
            linesRead += 500
            self.appendChunkToData(chunk)
            self._setStatusMessage("%i lines read" % linesRead)
            self._setProgress(linesRead/lineCount * 100)

        self._setStatusMessage("File loaded")
        self._setProgress(100)
        

    def appendChunkToData(self,chunk):
        if self.data is None:
            self.data = chunk
        else:
            self.data = pd.concat([self.data,chunk])
        
        self._emitDataChanged()
        
    def loadDataFromFileAsync(self,fileName):
        self._setCurrentFile(fileName)
        that = self
        class DataLoaderThread(q.QThread):
            def run(self):
                that.loadDataFromFile(fileName)


        thread = DataLoaderThread()
        thread.start()
        return thread

    @property
    def currentFile(self):
        return self._currentFile

    def _setCurrentFile(self,fileName):
        self._currentFile = fileName
        self.sourceChanged.emit(fileName)   
       
      

class FeatureTracker(q.QObject):

    __featureTrackers = []

    @classmethod
    def register(cls,childClass):
        cls.__featureTrackers.append(childClass)
        return childClass

    @classmethod
    def getRegisteredFeatureTrackers(cls):
        return [ft for ft in cls.__featureTrackers]

    @classmethod
    def getDisplayName(cls):
        return str(cls)

    def __init__(self):
        q.QObject.__init__(self)
        
    
    def findPosition(self,intensityProfile):
        raise NotImplemented("Implement this method in child class")
        
    

@FeatureTracker.register
class CurveFitTracker(FeatureTracker):

    @classmethod
    def getDisplayName(cls):
        return "Curve-fit"

    def __init__(self):
        FeatureTracker.__init__(self)
        self.fitFunction = None     
        
        
    def findPosition(self,intensityProfile):
        #TODO: implement        
        return 0

@FeatureTracker.register
class FFTPhaseShiftTracker(FeatureTracker):
    
    @classmethod
    def getDisplayName(cls):
        return "FFT phase shift"
    
    def __init__(self):
        FeatureTracker.__init__(self)
        
    def findPosition(self, intensityProfile):
        """
        TODO: implement
        """
        return super(FFTTracker, self).findPosition(intensityProfile)



class TrackableFeature(q.QObject):
    def __init__(self,name):
        super(TrackableFeature,self).__init__()
        
        self.name = name
        self.lowerLimit = 0        
        self.upperLimit = 0        
        self._tracker = FeatureTracker()
        
    @property
    def tracker(self):
        return self._tracker
    
    def setTracker(self,tracker):
        self._tracker = tracker
    
    
    
    def findPosition(self, data):
        """
        Searches the data within the limits for the feature using the tracker
        """
        self.tracker.findPosition(data[self.slice])

    def setLowerLimit(self,value):
        self.lowerLimit = value

    def setUpperLimit(self,value):
        self.upperLimit = value
        


        

        
    