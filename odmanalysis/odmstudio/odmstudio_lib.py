from PyQt4 import QtCore as q
from PyQt4 import QtGui as qt
import pandas as pd
import numpy as np
import odmanalysis as odm
from functools import wraps
from odmstudio_framework import RegisterSourceReader
import cv2
   
    

class SourceReader(q.QObject):
    
    dataChanged = q.pyqtSignal(pd.DataFrame)
    sourceChanged = q.pyqtSignal(str)
    statusMessageChanged = q.pyqtSignal(str)
    progressChanged = q.pyqtSignal(int)
    
    def __init__(self):
        super(SourceReader,self).__init__()
        self.data = None
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

        
    def _emitDataChanged(self):
        self.dataChanged.emit(self.data)

    def read(self,path):
        """
        Read data from path synchronously.

        Override this method to implement the logic for reading from the path. Make sure to call this super method before doing anything else.
        """
        
        self.data = None
        self._setCurrentPath(path)

        

    @property
    def currentPath(self):
        return self._currentPath

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

    @property
    def rangeSlice(self):
        return slice(self.xmin,self.xmax)

    



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
        


        

        
    