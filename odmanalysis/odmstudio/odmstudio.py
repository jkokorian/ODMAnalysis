from PyQt4 import QtCore as q
from PyQt4 import QtGui as qt
import pandas as pd
import numpy as np
import odmanalysis as odm





class SourceReader(q.QObject):
    
    dataChanged = q.pyqtSignal(pd.DataFrame)
    
    def __init__(self):
        super(SourceReader,self).__init__()
        self.data = None
        
    def _emitDataChanged(self):
        self.dataChanged.emit(self.data)
        

class CsvReader(SourceReader):
    
    statusMessageChanged = q.pyqtSignal(str)
    
    def __init__(self):
        SourceReader.__init__(self)
        self._statusMessage = ""
        
    @property
    def statusMessage(self):
        return self._statusMessage
        
    
    def _setStatusMessage(self,message):
        self._statusMessage = message
        self.statusMessageChanged.emit(message)


    def loadDataFromFile(self,filename):
        self.status = "busy"
        reader = odm.getODMDataReader(filename)
        
        chunks = []
        for chunk in reader:
            chunks.append(chunk)
        
        df = pd.concat(chunks)
        self.data = df
        self._emitDataChanged()
        
        
class SourceReaderWidget(qt.QWidget):
    def __init__(self,parent=None):
        super(SourceReaderWidget,self).__init__(parent)
    
class CsvReaderWidget(SourceReaderWidget):
    def __init__(self,parent=None):
        SourceReaderWidget.__init__(self,parent)
        
        self.csvReader = CsvReader()
        
        #create ui components
        
        layout = qt.QVBoxLayout()
        self.browseButton = qt.QPushButton("Browse...",parent=self)
        self.statusMessageLabel = qt.QLabel("",parent=self)
        layout.addWidget(self.browseButton)
        layout.addWidget(self.statusMessageLabel)
        
        self.setLayout(layout)

        
        #connect signals and slots
        
        self.csvReader.statusMessageChanged.connect(self.statusMessageLabel.setText)
        
        
       
        
class Tracker(q.QObject):
    def __init__(self):
        q.QObject.__init__(self)
    
    def findPosition(self,intensityProfile):
        raise NotImplemented("Implement this method in child class")
        
    
class CurveFitTracker(Tracker):
    def __init__(self):
        Tracker.__init__(self)
        self.fitFunction = None     
        
        
    def findPosition(self,intensityProfile):
        pass
        
class TrackableFeature(q.QObject):
    def __init__(self,name,lowerLimit,upperLimit):
        super(TrackableFeature,self).__init__()
        
        self.name = name
        self.slice = slice(lowerLimit,upperLimit)
        self.tracker = None
    
    def findPosition(self, data):
        """
        Searches the data within the limits for the feature using the tracker
        """
        self.tracker.findPosition(data[self.slice])
        


        
        
        
        
        
        
        
        
    