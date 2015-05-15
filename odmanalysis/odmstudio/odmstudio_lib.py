from PyQt4 import QtCore as q
from PyQt4 import QtGui as qt
import pandas as pd
import numpy as np
import odmanalysis as odm
from functools import wraps
from odmstudio_framework import RegisterSourceReader, CancellableWorkerThread
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

    def read(self,path,cancellationToken=None):
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
        class DataLoaderThread(CancellableWorkerThread):
            def __init__(self):
                CancellableWorkerThread.__init__(self)

            def run(self):
                that.read(path,cancellationToken = self.cancellationToken)



        thread = DataLoaderThread()
        thread.start()
        
        
        return thread


@RegisterSourceReader("Video files", extensions=('avi','mpg'), maxNumberOfFiles=1)
class VideoReader(SourceReader):

    def __init__(self):
        SourceReader.__init__(self)
        
        self._aoi = (0,0,100,100) #x_left,y_top,width,height
        self.summingAxis = 0

    def read(self, paths, cancellationToken=None):
        
        path = paths
        super(VideoReader, self).read(path)

        vid = cv2.VideoCapture(path)

        frameCount = int(vid.get(7))
        frameRate = vid.get(5)
        frameSize = (vid.get(3),vid.get(4))
        
        np.arange(frameCount)/frameRate

        framesRead = 0
        intensityProfiles = []
        timeSteps = np.arange(frameCount)/frameRate

        for i in range(frameCount):
            result, frame = vid.read()
            frameAOIGrayscale = frame[self.aoiSlices[0],self.aoiSlices[1],:].sum(axis=2)
            line = frameAOIGrayscale.sum(axis=self.summingAxis)
            #self.data.set_value(i,'intensityProfile', line)
            intensityProfiles.append(line)

            framesRead += 1
            self.data = pd.DataFrame(data={'intensityProfile': intensityProfiles, 'timeStep': timeSteps[0:framesRead]})

            self._setProgress((framesRead*100)/frameCount)
            self._setStatusMessage("%i frames read" % framesRead)
            self._emitDataChanged()

            if cancellationToken and cancellationToken.isCancellationRequested:
                break

        
        
        self._setStatusMessage("file loaded")
        self._setProgress(100)
    
    

    @property
    def aoiSlices(self):
        return (slice(self._aoi[0],self._aoi[0] + self._aoi[2]), slice(self._aoi[1],self._aoi[1] + self._aoi[3]))
        



@RegisterSourceReader("Comma separated", extensions=['csv'],maxNumberOfFiles=1)
class CsvReader(SourceReader):
    
    

    def __init__(self):
        SourceReader.__init__(self)
        

    def read(self,path,cancellationToken=None):
        super(CsvReader, self).read(path)
        
        self._setStatusMessage("reading...")
        reader = odm.getODMDataReader(path,chunksize=500)
        
        lineCount = float(sum(1 for line in open(path)))
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
        


        

        
    