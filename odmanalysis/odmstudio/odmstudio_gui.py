from PyQt4 import QtCore as q
from PyQt4 import QtGui as qt
import pyqtgraph as pg
import pyqtgraph.dockarea as dock
import odmstudio_lib as lib
import pandas as pd
import numpy as np
import os




class WidgetFactory(object):
    
    __dict = {}
    
    @classmethod
    def registerWidget(cls,widgetClass,anyClass):
        cls.__dict[anyClass] = widgetClass

    @classmethod
    def getWidgetFor(cls,anyClass):
        if cls.__dict.has_key(anyClass):
            return cls.__dict[anyClass]
        else:
            return qt.QWidget

def __registerWidgets():
    WidgetFactory.registerWidget(CurveFitTrackerWidget,lib.CurveFitTracker)
    WidgetFactory.registerWidget(FFTPhaseShiftTrackerWidget,lib.FFTPhaseShiftTracker)


class PlotController(q.QObject):
    """
    Base class for anything that can control a pyqtgraph plot
    """

    def __init__(self,parent=None):
        q.QObject.__init__(self,parent=None)
        self.plotWidget = None

    def connectToPlotWidget(self,plotWidget):
        if (self.plotWidget is not None):
            self.disconnectPlotWidget()
        self.plotWidget = plotWidget

    
    def disconnectPlotWidget(self):
        self.plotWidget = None


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
        


class TrackableFeatureWidget(qt.QWidget,PlotController):
    """
    Form for defining a trackable feature
    """
    def __init__(self,trackableFeature,parent=None):
        qt.QWidget.__init__(self,parent)
        PlotController.__init__(self,parent)
        self._trackableFeature = trackableFeature
        self._canDisable = True
        self._featureTrackerIsEnabled = True
        
        layout = qt.QVBoxLayout()
        
        self.featureEnabledCheckBox = qt.QCheckBox("Enable")
        self.featureEnabledCheckBox.setChecked(True)
        layout.addWidget(self.featureEnabledCheckBox)

        hLayout = qt.QHBoxLayout()
        self.lowerLimitSpinBox = qt.QSpinBox()
        self.upperLimitSpinBox = qt.QSpinBox()
        hLayout.addWidget(self.lowerLimitSpinBox)
        hLayout.addWidget(self.upperLimitSpinBox)
        layout.addLayout(hLayout)

        self.trackerComboBox = qt.QComboBox()
        layout.addWidget(self.trackerComboBox)

        self.featureTrackerWidgetContainer = qt.QGridLayout()
        self.featureTrackerWidget = None
        self.availableFeatureTrackers = lib.FeatureTracker.getRegisteredFeatureTrackers()
        
        for tracker in self.availableFeatureTrackers:
            self.trackerComboBox.addItem(tracker.getDisplayName())
        
        self.updateFeatureTrackerWidget()

        layout.addLayout(self.featureTrackerWidgetContainer)
        self.setLayout(layout)
        

        #connect signals and slots
        self.featureEnabledCheckBox.stateChanged.connect(self.setFeatureTrackerEnabled)
        self.trackerComboBox.currentIndexChanged.connect(self.updateFeatureTrackerWidget)
        

    def connectToPlotWidget(self, plotWidget):
        super(TrackableFeatureWidget, self).connectToPlotWidget(plotWidget)
        plotitem = self.plotWidget.getPlotItem()
        self.createPlotRegion()

    
    def createPlotRegion(self):
        self.region = pg.LinearRegionItem(brush=pg.intColor(1,alpha=100))
        self.region.setZValue(10)
        self.regionLabel = pg.TextItem(self._trackableFeature.name,color=pg.intColor(1),
                                                 anchor=(0,1))
        self.regionLabel.setX(self.region.getRegion()[0])
        self.plotWidget.addItem(self.regionLabel)                
        self.plotWidget.addItem(self.region, ignoreBounds=True)
        self.region.sigRegionChanged.connect(self.handleRegionChanged)

    def disconnectPlotWidget(self):
        self.region.sigRegionChanged.disconnect(self.handleRegionChanged)
        return super(TrackableFeatureWidget, self).disconnectPlotWidget()


    
        

    def handleRegionChanged(self, r):
        self.regionLabel.setX(r.getRegion()[0])
        self.lowerLimitSpinBox.setValue(r.getRegion()[0])
        self.upperLimitSpinBox.setValue(r.getRegion()[1])

    def updateFeatureTrackerWidget(self):
        if (self.featureTrackerWidget is not None):
            self.featureTrackerWidgetContainer.removeWidget(self.featureTrackerWidget)
            self.featureTrackerWidget.disconnectPlotWidget()
            self.featureTrackerWidget.setParent(None)

        self.featureTracker = self.availableFeatureTrackers[self.trackerComboBox.currentIndex()]
        self.featureTrackerWidget = WidgetFactory.getWidgetFor(self.featureTracker)(parent=self)
        if (self.featureTrackerWidget is PlotController):
            self.featureTrackerWidget.connectToPlotWidget(self.plotWidget)
        self.featureTrackerWidgetContainer.addWidget(self.featureTrackerWidget)
        

    def setCanDisable(self,canDisable):
        """
        Sets whether or not the "enable" checkbox should be shown on this widget.
        """
        self._canDisable = (canDisable == True)
        
    def getCanDisable(self):
        return self._canDisable

    def setFeatureTrackerEnabled(self,enabled):
        self._featureTrackerIsEnabled = (enabled == True)


        

class CurveFitTrackerWidget(qt.QWidget,PlotController):
    def __init__(self,parent=None):
        qt.QWidget.__init__(self,parent)
        PlotController.__init__(self,parent)
        layout = qt.QVBoxLayout()
        self.groupbox = qt.QGroupBox("Curve-fit settings")
        layout.addWidget(self.groupbox)
        self.setLayout(layout)

    def connectToPlotWidget(self, plotWidget):
        return super(CurveFitTrackerWidget, self).connectToPlotWidget(plotWidget)

    def disconnectPlotWidget(self):
        pass

class FFTPhaseShiftTrackerWidget(qt.QWidget,PlotController):
    def __init__(self,parent=None):
        qt.QWidget.__init__(self,parent)
        PlotController.__init__(self,parent)
        layout = qt.QVBoxLayout()
        self.groupbox = qt.QGroupBox("FFT phase-shift settings")
        layout.addWidget(self.groupbox)
        self.setLayout(layout)

    def connectToPlotWidget(self, plotWidget):
        return super(CurveFitTrackerWidget, self).connectToPlotWidget(plotWidget)

    def disconnectPlotWidget(self):
        pass
    
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
        

class ODMStudioMainWindow(qt.QMainWindow):

    fileDropped = q.pyqtSignal(str)

    def __init__(self,parent=None):
        qt.QMainWindow.__init__(self,parent)
        
        self.setWindowTitle("ODM Studio")
        self.resize(800,600)
        self.setAcceptDrops(True)

        area=dock.DockArea()
        self.dockArea = area
        self.setCentralWidget(area)


        self.displacementPlot = DisplacementPlotWidget(self)
        self.sourceReaderWidget = CsvReaderWidget(self)
        self.intensityProfilePlot = IntensityProfilePlotWidget(self)

        movingFeature = lib.TrackableFeature("moving feature")
        referenceFeature = lib.TrackableFeature("reference feature")        
        
        self.movingFeatureWidget = TrackableFeatureWidget(movingFeature,parent=self)
        self.referenceFeatureWidget = TrackableFeatureWidget(referenceFeature,parent=self)
        self.movingFeatureWidget.connectToPlotWidget(self.intensityProfilePlot.plotWidget)
        self.referenceFeatureWidget.connectToPlotWidget(self.intensityProfilePlot.plotWidget)

        
        sourceReaderDock = dock.Dock("Source Reader", size=(200,400))
        area.addDock(sourceReaderDock, 'left')      ## place d1 at left edge of dock area (it will fill the whole space since there are no other docks yet)
        sourceReaderDock.addWidget(self.sourceReaderWidget)
        
        intensityProfileDock = dock.Dock("Intensity Profiles", size=(500, 500))     ## give this dock the minimum possible size
        area.addDock(intensityProfileDock, 'right', sourceReaderDock)     ## place d2 at right edge of dock area
        intensityProfileDock.addWidget(self.intensityProfilePlot)
        
        displacementGraphDock = dock.Dock("Displacement Graph", size=(500,500))
        area.addDock(displacementGraphDock, 'bottom', intensityProfileDock)## place d3 at bottom edge of d1
        displacementGraphDock.addWidget(self.displacementPlot)
        
        featureTrackersDock = dock.Dock("Feature Trackers", size=(100,400))
        area.addDock(featureTrackersDock, 'right', intensityProfileDock)
        featureTrackersDock.addWidget(self.movingFeatureWidget)
        featureTrackersDock.addWidget(self.referenceFeatureWidget)



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