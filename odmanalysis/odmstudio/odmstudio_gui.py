from PyQt4 import QtCore as q
from PyQt4 import QtGui as qt
import pyqtgraph as pg
import odmstudio_lib as lib
import pandas as pd
import numpy as np
import os

class SourceReaderWidget(qt.QWidget):
    def __init__(self,parent=None):
        super(SourceReaderWidget,self).__init__(parent)
        

    @property
    def sourceReader(self):
        return self._sourceReader

    def handleDroppedFile(self,path):
        pass
    
class CsvReaderWidget(SourceReaderWidget):
    def __init__(self, parent=None):
        SourceReaderWidget.__init__(self,parent)
        
        self._sourceReader = lib.CsvReader()
        self.currentFile = ""
        self.readerThread = None

        #create ui components
        
        layout = qt.QVBoxLayout()
        self.browseButton = qt.QPushButton("Browse...",parent=self)
        self.currentFileLabel = qt.QLabel("No file open",parent=self)
        self.statusMessageLabel = qt.QLabel("",parent=self)
        layout.addWidget(self.browseButton)
        layout.addWidget(self.statusMessageLabel)
        layout.addWidget(self.currentFileLabel)
        
        self.setLayout(layout)

        
        #connect signals and slots
        
        self._sourceReader.statusMessageChanged.connect(self.statusMessageLabel.setText)
        self.browseButton.clicked.connect(self.showBrowseDialog)
    

    def handleDroppedFile(self, path):
        self.readFileAsync(path)    

    def showBrowseDialog(self):
        fileName = qt.QFileDialog.getOpenFileName(self)
        if fileName is not None:
            self.readFileAsync(fileName)

    def readFileAsync(self,fileName):
        self.currentFile = fileName
        
        self.readerThread = self._sourceReader.loadDataFromFileAsync(str(fileName))
        


class TrackableFeatureWidget(qt.QWidget):
    """
    Form for defining a trackable feature
    """
    def __init__(self,trackableFeature,parent=None):
        qt.QWidget.__init__(self,parent)
        self.trackableFeature = trackableFeature

        
        
    
class IntensityProfilePlotWidget(qt.QWidget):
    

    def __init__(self,parent=None):        
        qt.QWidget.__init__(self,parent)
        
        
        layout = qt.QVBoxLayout()        
        self.setLayout(layout)
        
        hLayout = qt.QHBoxLayout()
        layout.addLayout(hLayout)
        
        self.stepSlider = qt.QSlider(q.Qt.Horizontal)
        self.stepSlider.setTickPosition(qt.QSlider.TicksBothSides)
        self.stepSlider.setTickInterval(1)
        
        self.stepSpinBox = qt.QSpinBox()
        
        hLayout.addWidget(self.stepSpinBox)
        hLayout.addWidget(self.stepSlider)
        
                
        self.plotWidget = pg.PlotWidget()
        layout.addWidget(self.plotWidget)
        
        self.__initializePlots() 

        df = pd.DataFrame(data={'intensityProfile': []})
        
        
        self.df = df

        self._updateControlLimits()

        

        # connect signals
        self.stepSlider.valueChanged.connect(self.showStep)
        self.stepSlider.valueChanged.connect(self.stepSpinBox.setValue)
        self.stepSpinBox.valueChanged.connect(self.showStep)
        self.stepSpinBox.valueChanged.connect(self.stepSlider.setValue)
        

    def _updateControlLimits(self):
        self.stepSlider.setMinimum(0)
        self.stepSlider.setMaximum(len(self.df) - 1)
        self.stepSpinBox.setMinimum(0)
        self.stepSpinBox.setMaximum(len(self.df) - 1)
    
    def showStep(self,stepNumber):
        df = self.df
        ip = df.intensityProfile.iloc[stepNumber]
        ip = ip - ip.mean()
        
        self.dataPlot.setData(x=np.arange(len(ip)),y=ip)
        
        
    def __initializePlots(self):
        pw = self.plotWidget
        self.dataPlot = pw.plot()
        self.dataPlot.setPen((200,200,100))
        
        self.movingPeakFitPlot = pw.plot()
        self.movingPeakFitPlot.setPen((200,0,0))
        self.referencePeakFitPlot = pw.plot()
        self.referencePeakFitPlot.setPen((0,200,0))
        self.xValues = []
        
        pw.setLabel('left', 'Intensity', units='a.u.')
        pw.setLabel('bottom', 'Position', units='px')
        pw.setXRange(0, 200)
        pw.setYRange(0, 10000)
        
        pw.setAutoVisible(y=True)
    
    def setData(self,dataframe):
        """
        Set the data source for plotting.
        """
        self.df = dataframe
        self._updateControlLimits()


        
    #def updateGraphData(self, fitFunction_mp, popt_mp,
    #fitFunction_ref,popt_ref):
    #    self.movingPeakFitPlot.setData(x=self.xValues,y=fitFunction_mp(self.xValues,*popt_mp))
        
    #    self.referencePeakFitPlot.setData(x=self.xValues,y=fitFunction_ref(self.xValues,*popt_ref))
    

class DisplacementPlotWidget(qt.QWidget):
    def __init__(self,parent=None):
        qt.QWidget.__init__(self,parent)
        layout = qt.QVBoxLayout()

        self.plotWidget = pg.PlotWidget()
        layout.addWidget(self.plotWidget)
        self.setLayout(layout)
        

class InteractiveTrackingWidget(qt.QWidget):

    fileDropped = q.pyqtSignal(str)

    def __init__(self,parent=None):
        qt.QWidget.__init__(self,parent)
        
        self.setAcceptDrops(True)

        self.displacementPlot = DisplacementPlotWidget(self)
        self.sourceReaderWidget = CsvReaderWidget(self)
        self.intensityProfilePlot = IntensityProfilePlotWidget(self)

        movingFeature = lib.TrackableFeature("moving feature")
        referenceFeature = lib.TrackableFeature("reference feature")        
        
        self.movingFeatureWidget = TrackableFeatureWidget(movingFeature,parent=self)
        self.referenceFeatureWidget = TrackableFeatureWidget(referenceFeature,parent=self)
        

        lvLayout = qt.QVBoxLayout()
        lvLayout.addWidget(self.sourceReaderWidget)
        lvLayout.addWidget(self.intensityProfilePlot)
        lvLayout.addWidget(self.displacementPlot)
        
        rvLayout = qt.QHBoxLayout()
        rvLayout.addWidget(self.movingFeatureWidget)
        rvLayout.addWidget(self.referenceFeatureWidget)


        hLayout = qt.QHBoxLayout()
        hLayout.addLayout(lvLayout)
        hLayout.addLayout(rvLayout)
        
        self.setLayout(hLayout)


        #connect signals and slots
        
        self.sourceReaderWidget.sourceReader.dataChanged.connect(self.intensityProfilePlot.setData)
        self.fileDropped.connect(self.sourceReaderWidget.handleDroppedFile)


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()


    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(q.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile().toLocal8Bit().data()
            if os.path.isfile(path):
                self._emitFileDropped(path)

    def _emitFileDropped(self,path):
        self.fileDropped.emit(path)

def logToConsole(message):
    print message