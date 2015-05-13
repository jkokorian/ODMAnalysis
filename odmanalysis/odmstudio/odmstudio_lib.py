from PyQt4 import QtCore as q
from PyQt4 import QtGui as qt
import pandas as pd
import numpy as np
import odmanalysis as odm
from functools import wraps





class RegisterSourceReader(object):
    """
    Decorate classes that inherit from SourceReader with this method to indicate what kind of files the sourcereader handles.
    """

    _sourceReaders = {}

    @classmethod
    def getSourceReaderForFileType(cls, fileType): 
        return cls._sourceReaders[fileType]
    
    @classmethod
    def hasSourceReaderForFileType(cls,fileType):
        return cls._sourceReaders.has_key(fileType)

    def __init__(self, fileType, maxNumberOfFiles=1):
        self.fileType = fileType
        self.maxNumberOfFiles = maxNumberOfFiles;

    def __call__(self,cls):
        self._sourceReader = cls
        RegisterSourceReader._sourceReaders[self.fileType] = self
        
        return cls

    def getNewSourceReader(self):
        return self._sourceReader;


class SourceReader(q.QObject):
    
    dataChanged = q.pyqtSignal(pd.DataFrame)
    sourceChanged = q.pyqtSignal(str)

    
    def __init__(self):
        super(SourceReader,self).__init__()
        self.data = None
        self._currentPath = ""
        
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
        self.sourceChanged.emit(path)   


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


@RegisterSourceReader(".avi")
class VideoReader(SourceReader):

    def __init__(self):
        SourceReader.__init__(self)
        pass

    def read(self, path):
        pass

    

@RegisterSourceReader(".csv")
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


    def read(self,path):
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
        
    
       
class FileOpener(q.QObject):
    """
    Takes care of creating and destroying sourcereader objects and their corresponding gui widgets.
    """

    sourceReaderChanged = q.pyqtSignal(SourceReader)
    dataChanged = q.pyqtSignal(pd.DataFrame)
    sourcePathChanged = q.pyqtSignal(str)

    def __init__(self,sourceReaderWidgetContainer):
        """
        parameters:
        -----------

        sourceReaderWidgetContainer: a container object in which the source reader widgets can be placed
        """
        
        super(SourceReader,self).__init__()
        
        self.sourceReaderWidgetContainer = sourceReaderWidgetContainer;
        self.__sourceReader = None
        
    def openFiles(paths):
        singleExtension = len(set([os.path.splitext(path)[-1] for path in paths])) == 1
        
        if (singleExtension):
            ext = os.path.splitext(paths[0])[-1]
            if os.path.isfile(path) and RegisteredSourceReader.hasSourceReaderForFileType(ext):
                registeredSourceReader = RegisteredSourceReader.getSourceReaderForFileType(ext)
                if registeredSourceReader.maxNumberOfFiles >= len(paths):
                    self.sourceReader = registeredSourceReader.getNewSourceReader();
                    
                
                
        else:
            #cannot handle multiple file extensions being dropped simultaneously
            pass
     
    @property
    def sourceReader(self):
        return self.__sourceReader;

    @sourceReader.setter
    def sourceReader(self,sourceReader):
        if self.__sourceReader is not None:
            self.__sourceReader.dataChanged.disconnect(self._sourceReader_dataChanged)
            self.__sourceReader.sourceChanged.disconnect(self._sourceReader_sourceChanged)
        
        self.__sourceReader = sourceReader;
        sourceReader.dataChanged.connect(self._sourceReader_dataChanged)
        sourceReader.sourceChanged.connect(self._sourceReader_sourceChanged)

        self.sourceReaderChanged.emit(self.__sourceReader)
    
    def _sourceReader_dataChanged(self,df):
        self.dataChanged.emit(df)

    def _sourceReader_sourceChanged(self,path):
        self.sourcePathChanged.emit(path)      

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
        


        

        
    