from PyQt4 import QtCore as q
from PyQt4 import QtGui as qt
import pyqtgraph as pg
import pyqtgraph.dockarea as dock
import odmstudio_lib as lib
import pandas as pd
import numpy as np
import os
from odmanalysis.odmstudio.odmstudio_framework import *



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
    """
    Decorate classes that use this class as a base with the RegisterWidgetFor decorator, to indicate for sourcereader it handles.
    """    
    def __init__(self,sourceReader,parent=None):
        super(SourceReaderWidget,self).__init__(parent)
        

    @property
    def sourceReader(self):
        return self._sourceReader


       

class FileOpener(qt.QWidget):
    """
    Takes care of creating and destroying sourcereader objects and their corresponding gui widgets.
    """

    sourceReaderChanged = q.pyqtSignal(lib.SourceReader)
    dataChanged = q.pyqtSignal(pd.DataFrame)
    sourcePathChanged = q.pyqtSignal(str)
    progressChanged = q.pyqtSignal(int)
    statusMessageChanged = q.pyqtSignal(str)


    def __init__(self,parent=None):
        """
        parameters:
        -----------

        sourceReaderWidgetContainer: a container object in which the source reader widgets can be placed
        """
        
        super(qt.QWidget,self).__init__(parent=parent)
        
        self.sourceReaderWidget = None
        self.__sourceReader = None
        self.__statusMessage = ""
        self.__readerThread = None

        #actions
        self.openFileAction = qt.QAction(self.style().standardIcon(qt.QStyle.SP_DialogOpenButton),"Open file...",self)
        

        #connect signals and slots
        self.openFileAction.triggered.connect(self.showOpenFileDialog)

    
    def showOpenFileDialog(self):
        extensionsFilter = ";;".join([srr.getFilterString() for srr in SourceReaderFactory.getSourceReaderRegistrations()])
        fileName = qt.QFileDialog.getOpenFileName(parent=None,caption="open file...",directory="",filter=extensionsFilter)
        self.tryOpenFiles([fileName])

    def tryOpenFiles(self,paths):
        try:
            self.openFiles([str(path) for path in paths]) #explicit conversion from QString to str, otherwise os.path.* function fail.
        except:
            self._setStatusMessage("Unable to open file(s)")

    def openFiles(self,paths):
        singleExtension = len(set([os.path.splitext(path)[-1] for path in paths])) == 1
        
        assert singleExtension

        ext = os.path.splitext(paths[0])[-1][1:]
        
        assert SourceReaderFactory.hasSourceReaderForExtension(ext)

        srRegistration = SourceReaderFactory.getSourceReaderForExtension(ext)

        assert srRegistration.maxNumberOfFiles >= len(paths)


        #set source reader
        self.sourceReader = srRegistration.sourceReaderType();


        SRWidget = WidgetFactory.getWidgetClassFor(srRegistration.sourceReaderType)
        

        if SRWidget is not None:
            self.sourceReaderWidget = SRWidget(self.sourceReader,parent=self)
            #TODO: show the SourceReader Widget in a dialog

        else:
            self.sourceReaderWidget = None
            
            # if there is no widget defined for the target SourceReader, read the files to open immediately
            if len(paths) == 1:
                self.__readerThread = self.sourceReader.readAsync(paths[0])
            else:
                self.__readerThread = self.sourceReader.readAsync(paths)
            
                
     
    @property
    def sourceReader(self):
        return self.__sourceReader;

    @sourceReader.setter
    def sourceReader(self,sourceReader):
        #disconnect current sourcereader
        if self.__sourceReader is not None:
            self.__sourceReader.dataChanged.disconnect(self.__sourceReader_dataChanged)
            self.__sourceReader.sourceChanged.disconnect(self.__sourceReader_sourceChanged)
            self.__sourceReader.statusMessageChanged.disconnect(self._setStatusMessage)
            self.__sourceReader.progressChanged.disconnect(self.__sourceReader_progressChanged)
        
        #connect new sourcereader
        self.__sourceReader = sourceReader;
        self.__sourceReader.dataChanged.connect(self.__sourceReader_dataChanged)
        self.__sourceReader.sourceChanged.connect(self.__sourceReader_sourceChanged)
        self.__sourceReader.statusMessageChanged.connect(self._setStatusMessage)
        self.__sourceReader.progressChanged.connect(self.__sourceReader_progressChanged)

        self.sourceReaderChanged.emit(self.__sourceReader)
    
    def __sourceReader_dataChanged(self,df):
        self.dataChanged.emit(df)

    def __sourceReader_sourceChanged(self,path):
        self.sourcePathChanged.emit(path)

    def __sourceReader_statusMessageChanged(self,message):
        self.statusMessageChanged.emit(message)

    def __sourceReader_progressChanged(self,progress):
        self.progressChanged.emit(progress)

    @property
    def statusMessage(self):
        return self.__statusMessage

    def _setStatusMessage(self,message):
        self.__statusMessage = message
        self.statusMessageChanged.emit(message)

                
         
class FeatureTrackerControlsWidget(qt.QWidget):

    featureTrackerChanged = q.pyqtSignal(lib.FeatureTracker)

    def __init__(self,parent=None,featureTracker=None):
        qt.QWidget.__init__(self,parent)

        self._featureTracker = featureTracker

        layout = qt.QHBoxLayout()
        

        self.initializeAction = qt.QAction(self.style().standardIcon(qt.QStyle.SP_BrowserReload),"Initialize",self)
        self.findInCurrentProfileAction = qt.QAction(self.style().standardIcon(qt.QStyle.SP_MediaPlay),"Find in current profile",self)
        self.findInAllProfilesAction = qt.QAction(self.style().standardIcon(qt.QStyle.SP_MediaSeekForward),"Find in all profiles",self)

        self.initializeButton = qt.QToolButton(self)
        self.initializeButton.setDefaultAction(self.initializeAction)
        self.findInCurrentProfileButton = qt.QToolButton(self)
        self.findInCurrentProfileButton.setDefaultAction(self.findInCurrentProfileAction)
        self.findInAllProfilesButton = qt.QToolButton(self)
        self.findInAllProfilesButton.setDefaultAction(self.findInAllProfilesAction)
        

        
        layout.addStretch()
        layout.addWidget(self.initializeButton)
        layout.addWidget(self.findInCurrentProfileButton)
        layout.addWidget(self.findInAllProfilesButton)
        
        self.setLayout(layout)
        

    def setFeatureTracker(self,featureTracker):
        self._featureTracker = featureTracker
        self.featureTrackerChanged.emit(featureTracker)

    def getFeatureTracker(self):
        return self._featureTracker



class TrackableFeatureWidget(qt.QWidget,PlotController):
    """
    Form for defining a trackable feature
    """

    sourceDataChanged = q.pyqtSignal(pd.DataFrame)

    def __init__(self,trackableFeature,parent=None):
        qt.QWidget.__init__(self,parent)
        PlotController.__init__(self,parent)
        self._trackableFeature = trackableFeature
        self._canDisable = True
        self._featureTrackerIsEnabled = True
        self._sourceData = None

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
        self.availableFeatureTrackers = FeatureTrackerFactory.getFeatureTrackers()
        
        for tracker in self.availableFeatureTrackers:
            self.trackerComboBox.addItem(tracker.getDisplayName())
                

        layout.addLayout(self.featureTrackerWidgetContainer)
        
        self.featureTrackerControlsWidget = FeatureTrackerControlsWidget(self)
        layout.addWidget(self.featureTrackerControlsWidget)
        self.setLayout(layout)
        
        
        self.updateFeatureTrackerWidget()

        #connect signals and slots
        self.featureEnabledCheckBox.stateChanged.connect(self.setFeatureTrackerEnabled)
        self.trackerComboBox.currentIndexChanged.connect(self.handleFeatureTrackerSelected)
        

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
        self.region.sigRegionChanged.connect(self.region_RegionChanged)

    def disconnectPlotWidget(self):
        self.region.sigRegionChanged.disconnect(self.region_RegionChanged)
        return super(TrackableFeatureWidget, self).disconnectPlotWidget()
        

    def region_RegionChanged(self, r):
        self.regionLabel.setX(r.getRegion()[0])
        self.lowerLimitSpinBox.setValue(r.getRegion()[0])
        self.upperLimitSpinBox.setValue(r.getRegion()[1])

    def updateFeatureTrackerWidget(self):
        if (self.featureTrackerWidget is not None):
            self.featureTrackerWidgetContainer.removeWidget(self.featureTrackerWidget)
            self.featureTrackerWidget.disconnectPlotWidget()
            self.featureTrackerWidget.setParent(None)

        self.featureTracker = self.availableFeatureTrackers[self.trackerComboBox.currentIndex()]
        featureTrackerWidgetType = WidgetFactory.getWidgetClassFor(self.featureTracker)
        if (featureTrackerWidgetType is not None):
            self.featureTrackerWidget = featureTrackerWidgetType(parent=None)
            if (self.featureTrackerWidget is PlotController):
                self.featureTrackerWidget.connectToPlotWidget(self.plotWidget)
            self.featureTrackerWidgetContainer.addWidget(self.featureTrackerWidget)
        
    def handleFeatureTrackerSelected(self):
        self.featureTrackerControlsWidget.setFeatureTracker(self.featureTracker)
        self.updateFeatureTrackerWidget()

    def setCanDisable(self,canDisable):
        """
        Sets whether or not the "enable" checkbox should be shown on this widget.
        """
        self._canDisable = (canDisable == True)
        
    def getCanDisable(self):
        return self._canDisable

    def setFeatureTrackerEnabled(self,enabled):
        self._featureTrackerIsEnabled = (enabled == True)


    def setSourceData(self,dataframe):
        self._sourceData = dataframe
        self.updateFormElements()
        
        
    def getSourceData(self):
        return self._sourceData

    def updateFormElements(self):
        if (self._sourceData is not None):
            xMaximum = len(self._sourceData.intensityProfile.iloc[0])
            self.lowerLimitSpinBox.setMaximum(xMaximum)
            self.upperLimitSpinBox.setMaximum(xMaximum)


    



class TrackableFeatureControlWidget(qt.QWidget,PlotController):
    def __init__(self,parent=None):
        qt.QWidget.__init__(self,parent)
        PlotController.__init__(self,parent)


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
    
    def setSourceData(self,dataframe):
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

    filesDropped = q.pyqtSignal(list)

    def __init__(self,parent=None):
        qt.QMainWindow.__init__(self,parent)
        
        self.setWindowTitle("ODM Studio")
        self.resize(800,600)
        self.setAcceptDrops(True)

        area=dock.DockArea()
        self.dockArea = area
        self.setCentralWidget(area)


        self.displacementPlot = DisplacementPlotWidget(self)
        self.fileOpener = FileOpener(self)
        self.intensityProfilePlot = IntensityProfilePlotWidget(self)

        movingFeature = lib.TrackableFeature("moving feature")
        referenceFeature = lib.TrackableFeature("reference feature")        
        
        self.movingFeatureWidget = TrackableFeatureWidget(movingFeature,parent=self)
        self.referenceFeatureWidget = TrackableFeatureWidget(referenceFeature,parent=self)
        self.movingFeatureWidget.connectToPlotWidget(self.intensityProfilePlot.plotWidget)
        self.referenceFeatureWidget.connectToPlotWidget(self.intensityProfilePlot.plotWidget)

        
        
        intensityProfileDock = dock.Dock("Intensity Profiles", size=(500, 500))     ## give this dock the minimum possible size
        area.addDock(intensityProfileDock, 'left')     ## place d2 at left of dock area
        intensityProfileDock.addWidget(self.intensityProfilePlot)
        
        displacementGraphDock = dock.Dock("Displacement Graph", size=(500,500))
        area.addDock(displacementGraphDock, 'bottom', intensityProfileDock)## place d3 at bottom edge of d1
        displacementGraphDock.addWidget(self.displacementPlot)
        
        featureTrackersDock = dock.Dock("Feature Trackers", size=(100,400))
        area.addDock(featureTrackersDock, 'right', intensityProfileDock)
        featureTrackersDock.addWidget(self.movingFeatureWidget)
        featureTrackersDock.addWidget(self.referenceFeatureWidget)


        #setup statusbar
        self.progressBar = qt.QProgressBar()
        self.statusBar().addPermanentWidget(self.progressBar)


        #setup menubar
        self.menuBar().addAction(self.fileOpener.openFileAction)


        #connect signals and slots
        self.filesDropped.connect(self.fileOpener.tryOpenFiles)
        
        self.fileOpener.dataChanged.connect(self.intensityProfilePlot.setSourceData)
        self.fileOpener.dataChanged.connect(self.movingFeatureWidget.setSourceData)
        self.fileOpener.dataChanged.connect(self.referenceFeatureWidget.setSourceData)
        self.fileOpener.sourcePathChanged.connect(self.setWindowTitle)
        self.fileOpener.statusMessageChanged.connect(self.logMessage)
        self.fileOpener.progressChanged.connect(self.logProgress)

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
        paths = [url.toLocalFile().toLocal8Bit().data() for url in event.mimeData().urls()]
        paths = [path for path in paths if os.path.isfile(path)]
        if paths:
            self.filesDropped.emit(paths)


    def logMessage(self,message):
        self.statusBar().showMessage(message,1000)

    def logProgress(self,progress):
        self.progressBar.setValue(progress)
    

def logToConsole(message):
    print message