import PyQt4.QtCore as q
import PyQt4.QtGui as qt
import pyqtgraph as pg
import pyqtgraph.dockarea as dock
import odmanalysis.odmstudio.odmstudio_lib as lib
import odmanalysis.odmstudio.odmstudio_framework as fw
import pandas as pd
import numpy as np
import os
from odmanalysis.odmstudio.observable import Observer


class PlotController(q.QObject):
    """
    Mixin class for anything that can control a pyqtgraph plot
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

    progressChanged = q.pyqtSignal(int)
    statusMessageChanged = q.pyqtSignal(str)


    def __init__(self,dataSource,parent=None):
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
        assert isinstance(dataSource,lib.DataSource)
        self.__dataSource = dataSource

        #actions
        self.openFileAction = qt.QAction(self.style().standardIcon(qt.QStyle.SP_DialogOpenButton),"Open data-source...",self,shortcut=qt.QKeySequence.Open)
        

        #connect signals and slots
        self.openFileAction.triggered.connect(self.showOpenFileDialog)

    
    def showOpenFileDialog(self):
        extensionsFilter = ";;".join([srr.getFilterString() for srr in fw.SourceReaderFactory.getSourceReaderRegistrations()])
        fileName = qt.QFileDialog.getOpenFileName(parent=None,caption="open file...",directory="",filter=extensionsFilter)
        if fileName:
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
        
        assert fw.SourceReaderFactory.hasSourceReaderForExtension(ext)

        srRegistration = fw.SourceReaderFactory.getSourceReaderForExtension(ext)

        assert srRegistration.maxNumberOfFiles >= len(paths)


        #set source reader
        self.sourceReader = srRegistration.sourceReaderType(self.__dataSource)


        SRWidget = fw.WidgetFactory.getWidgetClassFor(srRegistration.sourceReaderType)
        

        if SRWidget is not None:
            self.sourceReaderWidget = SRWidget(self.sourceReader,parent=self)
            #TODO: show the SourceReader Widget in a dialog

        else:
            self.sourceReaderWidget = None
            
            # if there is no widget defined for the target SourceReader, read
            # the files to open immediately
            if len(paths) == 1:
                self.__readerThread = self.sourceReader.readAsync(paths[0])
            else:
                self.__readerThread = self.sourceReader.readAsync(paths)
            
                
    @property
    def statusMessage(self):
        return self.__statusMessage

    def _setStatusMessage(self,message):
        self.__statusMessage = message
        self.statusMessageChanged.emit(message)
     
    @property
    def sourceReader(self):
        return self.__sourceReader

    @sourceReader.setter
    def sourceReader(self,sourceReader):

        #disconnect current sourcereader
        if self.__sourceReader is not None:
            self.__sourceReader.statusMessageChanged.disconnect(self._setStatusMessage)
            self.__sourceReader.progressChanged.disconnect(self.__sourceReader_progressChanged)
        
        #connect new sourcereader
        self.__sourceReader = sourceReader
        self.__sourceReader.statusMessageChanged.connect(self._setStatusMessage)
        self.__sourceReader.progressChanged.connect(self.__sourceReader_progressChanged)

    
    @property
    def dataSource(self):
        return self.__dataSource

    def _setDataSource(self,dataSource):
        assert isinstance(dataSource,lib.DataSource)
        self.__dataSource = dataSource


    def __sourceReader_statusMessageChanged(self,message):
        self.statusMessageChanged.emit(message)

    def __sourceReader_progressChanged(self,progress):
        self.progressChanged.emit(progress)


                
         
class FeatureTrackerControlsWidget(qt.QWidget):

    featureTrackerChanged = q.pyqtSignal(lib.FeatureTracker)

    def __init__(self,parent=None,featureTracker=None):
        qt.QWidget.__init__(self,parent)

        self._featureTracker = featureTracker

        

        self.initializeAction = qt.QAction(self.style().standardIcon(qt.QStyle.SP_BrowserReload),"Initialize",self)
        self.findInCurrentProfileAction = qt.QAction(self.style().standardIcon(qt.QStyle.SP_MediaPlay),"Find in current profile",self)
        self.findInAllProfilesAction = qt.QAction(self.style().standardIcon(qt.QStyle.SP_MediaSeekForward),"Find in all profiles",self)

        layout = qt.QHBoxLayout()
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
        #self.featureTrackerChanged.emit(featureTracker)

    def getFeatureTracker(self):
        return self._featureTracker



class RegionSpinBoxControl(qt.QWidget):

    regionChanged = q.pyqtSignal(tuple)
    lowerLimitChanged  =q.pyqtSignal(int)
    upperLimitChanged = q.pyqtSignal(int)
    
    @property
    def region(self):
        return self.getRegion()

    def __init__(self,parent=None):
        qt.QWidget.__init__(self,parent)

        

        self.initializeUI()


    def initializeUI(self):
        layout = qt.QHBoxLayout()
        self.lowerLimitSpinBox = qt.QSpinBox()
        self.upperLimitSpinBox = qt.QSpinBox()
        layout.addWidget(self.lowerLimitSpinBox)
        layout.addWidget(self.upperLimitSpinBox)
        self.setLayout(layout)

        #connect signals
        self.lowerLimitSpinBox.valueChanged.connect(self._emitRegionChanged)
        self.upperLimitSpinBox.valueChanged.connect(self._emitRegionChanged)


    def getRegion(self):
        return (self.lowerLimitSpinBox.value(),self.upperLimitSpinBox.value())

    def setRegion(self,region):
        regionChanged = False
        
        if region[0] != self.region[0]:
            regionChanged = True
            self.lowerLimitSpinBox.setValue(region[0])
        if region[1] != self.region[1]:
            regionChanged = True
            self.upperLimitSpinBox.setValue(region[1])
        
        if regionChanged:
            self.regionChanged.emit(self.region)

    def getUpperLimit(self):
        return self.region[1]

    def getLowerLimit(self):
        return self.region[0]

    def setLowerLimit(self,value):
        if value != self.region[0]:
            self.lowerLimitSpinBox.setValue(value)
            self.lowerLimitChanged(self.getLowerLimit())
            self.regionChanged.emit(self.region)

    def setUpperLimit(self,value):
        if value != self.region[1]:
            self.upperLimitSpinBox.setValue(value)
            self.upperLimitChanged.emit(self.getUpperLimit())
            self.regionChanged.emit(self.region)

    def _emitRegionChanged(self):
        self.regionChanged.emit(self.region)

    def setSpinBoxMaxima(self,value):
        spinBoxes = [self.lowerLimitSpinBox,self.upperLimitSpinBox]
        for spinBox in spinBoxes:
            spinBox.setMaximum(value)

class TrackableFeatureWidget(qt.QWidget,PlotController):
    """
    Form for defining a trackable feature
    """

    _linearRegionItem_regionChanged = q.pyqtSignal(tuple)


    def __init__(self,trackableFeature,parent=None):
        qt.QWidget.__init__(self,parent)
        PlotController.__init__(self,parent)
        assert isinstance(trackableFeature, lib.TrackableFeature)
        self.__trackableFeature = trackableFeature
        self._canDisable = True
        self._featureTrackerIsEnabled = True
        self.availableFeatureTrackers = fw.FeatureTrackerFactory.getFeatureTrackers()


        #actions
        self.initializeTrackerAction = qt.QAction(self.style().standardIcon(qt.QStyle.SP_BrowserReload),"Initialize",self)
        self.locateInCurrentAction = qt.QAction(self.style().standardIcon(qt.QStyle.SP_MediaPlay),"Find in current profile",self)
        self.locateAllAction = qt.QAction(self.style().standardIcon(qt.QStyle.SP_MediaSeekForward),"Find in all profiles",self)

        #main layout
        layout = qt.QVBoxLayout()
        
        #featureEnabledCheckBox
        self.featureEnabledCheckBox = qt.QCheckBox("Enable")
        self.featureEnabledCheckBox.setChecked(True)
        layout.addWidget(self.featureEnabledCheckBox)

        
        #region limit SpinBoxes
        self.regionSpinBoxControl = RegionSpinBoxControl(self)
        layout.addWidget(self.regionSpinBoxControl)


        #featureTrackerComboBox
        self.featureTrackerComboBox = qt.QComboBox()
        layout.addWidget(self.featureTrackerComboBox)
        for tracker in self.availableFeatureTrackers:
            self.featureTrackerComboBox.addItem(tracker.getDisplayName())
        

        #featureTrackerWidgetContainer
        self.featureTrackerWidgetContainer = qt.QGridLayout()
        self.featureTrackerWidget = None
        layout.addLayout(self.featureTrackerWidgetContainer)
        

        #featureTrackerControls
        buttonsLayout = qt.QHBoxLayout()
        self.initializeButton = qt.QToolButton(self)
        self.initializeButton.setDefaultAction(self.initializeTrackerAction)
        self.findInCurrentProfileButton = qt.QToolButton(self)
        self.findInCurrentProfileButton.setDefaultAction(self.locateInCurrentAction)
        self.findInAllProfilesButton = qt.QToolButton(self)
        self.findInAllProfilesButton.setDefaultAction(self.locateAllAction)
        
        
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.initializeButton)
        buttonsLayout.addWidget(self.findInCurrentProfileButton)
        buttonsLayout.addWidget(self.findInAllProfilesButton)
        layout.addLayout(buttonsLayout)

        
        
        self.setLayout(layout)
        
        self.setFeatureTracker()



        #connect signals and slots
        self.featureEnabledCheckBox.stateChanged.connect(self.setFeatureTrackerEnabled)
        self.featureTrackerComboBox.currentIndexChanged.connect(self.setFeatureTracker)

        self.initializeTrackerAction.triggered.connect(self.trackableFeature.initializeTracker)
        self.locateAllAction.triggered.connect(self.trackableFeature.locateAllAsync)
        self.locateInCurrentAction.triggered.connect(self.trackableFeature.locateInCurrent)

        self.trackableFeature.dataSource.sourceDataChanged.connect(self.setRegionMaximum)


        #bind linear region item with model and spinboxes

        self.regionObserver = Observer()
        self.regionObserver.bind(self.regionSpinBoxControl,self.regionSpinBoxControl.getRegion,self.regionSpinBoxControl.setRegion,self.regionSpinBoxControl.regionChanged)
        self.regionObserver.bind(self.trackableFeature,self.trackableFeature.getRegion,self.trackableFeature.setRegion,self.trackableFeature.regionChanged)

    @property
    def trackableFeature(self):
        return self.__trackableFeature

        
    def setFeatureTracker(self):
        self.trackableFeature.setTracker(self.availableFeatureTrackers[self.featureTrackerComboBox.currentIndex()]())
        
        if (self.featureTrackerWidget is not None):
            self.featureTrackerWidgetContainer.removeWidget(self.featureTrackerWidget)
            self.featureTrackerWidget.disconnectPlotWidget()
            self.featureTrackerWidget.setParent(None)

        featureTrackerWidgetType = fw.WidgetFactory.getWidgetClassFor(self.trackableFeature.tracker)
        if (featureTrackerWidgetType is not None):
            self.featureTrackerWidget = featureTrackerWidgetType(parent=None)
            if (self.featureTrackerWidget is PlotController):
                self.featureTrackerWidget.connectToPlotWidget(self.plotWidget)
            self.featureTrackerWidgetContainer.addWidget(self.featureTrackerWidget)
        

    def connectToPlotWidget(self, plotWidget):
        super(TrackableFeatureWidget, self).connectToPlotWidget(plotWidget)
        plotitem = self.plotWidget.getPlotItem()
        self.createPlotRegion()

    
    def createPlotRegion(self):
        self.linearRegionItem = pg.LinearRegionItem(brush=pg.intColor(1,alpha=100))
        self.linearRegionItem.setZValue(10)
        self.regionLabel = pg.TextItem(self.trackableFeature.name, color=pg.intColor(1), anchor=(0,1))
        self.regionLabel.setX(self.linearRegionItem.getRegion()[0])
        self.plotWidget.addItem(self.regionLabel)
        self.plotWidget.addItem(self.linearRegionItem, ignoreBounds=True)
        self.linearRegionItem.sigRegionChanged.connect(self.linearRegionItem_RegionChanged)
        self.regionObserver.bind(self.linearRegionItem,self.linearRegionItem.getRegion,self.linearRegionItem.setRegion,self._linearRegionItem_regionChanged)

    def disconnectPlotWidget(self):
        self.linearRegionItem.sigRegionChanged.disconnect(self.linearRegionItem_RegionChanged)
        return super(TrackableFeatureWidget, self).disconnectPlotWidget()
        
    

    def linearRegionItem_RegionChanged(self, r):
        region = r.getRegion()
        self.regionLabel.setX(region[0])
        self._linearRegionItem_regionChanged.emit(region)
    
    
    

        
    def handleFeatureTrackerSelected(self):
        self.setFeatureTracker()

    def setCanDisable(self,canDisable):
        """
        Sets whether or not the "enable" checkbox should be shown on this widget.
        """
        self._canDisable = (canDisable == True)
        
    def getCanDisable(self):
        return self._canDisable

    def setFeatureTrackerEnabled(self,enabled):
        self._featureTrackerIsEnabled = (enabled == True)

    def setRegionMaximum(self):
        if not self.trackableFeature.dataSource.sourceIsEmpty:
            xMaximum = len(self.trackableFeature.dataSource.intensityProfiles.iloc[0])
            self.regionSpinBoxControl.setSpinBoxMaxima(xMaximum)

    
    
                


    






class IntensityProfilePlotWidget(qt.QWidget):

    @property
    def dataSource(self):
        return self.__dataSource

    def __init__(self,dataSource,parent=None):        
        qt.QWidget.__init__(self,parent)
        
        assert isinstance(dataSource,lib.DataSource)
        self.__dataSource = dataSource
        
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

        self._updateControlLimits()
        

        # connect signals
        self.stepSlider.valueChanged.connect(self.stepSpinBox.setValue)
        self.stepSpinBox.valueChanged.connect(self.dataSource.setCurrentIndexLocation)
        self.dataSource.currentIndexLocationChanged.connect(self.stepSlider.setValue)

        self.dataSource.currentIndexLocationChanged.connect(self.showStep)
        
        self.dataSource.sourceDataChanged.connect(self._updateControlLimits)
        

    
    
    def _updateControlLimits(self):
        self.stepSlider.setMinimum(0)
        self.stepSlider.setMaximum(self.dataSource.sourceLength - 1)
        self.stepSpinBox.setMinimum(0)
        self.stepSpinBox.setMaximum(self.dataSource.sourceLength - 1)
    
    def showStep(self,stepNumber):
        if self.dataSource.sourceLength > 0:
            ip = self.dataSource.intensityProfiles.iloc[stepNumber]
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
    
    

        
    #def updateGraphData(self, fitFunction_mp, popt_mp,
    #fitFunction_ref,popt_ref):
    #    self.movingPeakFitPlot.setData(x=self.xValues,y=fitFunction_mp(self.xValues,*popt_mp))
        
    #    self.referencePeakFitPlot.setData(x=self.xValues,y=fitFunction_ref(self.xValues,*popt_ref))
class DisplacementPlotWidget(qt.QWidget):

    @property
    def dataSource(self):
        return self.__dataSource

    def __init__(self, dataSource, parent=None):
        qt.QWidget.__init__(self, parent)

        assert isinstance(dataSource,lib.DataSource)
        self.__dataSource = dataSource

        layout = qt.QVBoxLayout()

        self.plotWidget = pg.PlotWidget()
        layout.addWidget(self.plotWidget)
        
        self.__initializePlots()

        self.setLayout(layout)


        #connect signals
        self.dataSource.resultDataChanged.connect(self.updatePlot)

    def __initializePlots(self):
        pw = self.plotWidget
        
        self.dataPlot = pw.plot()
        self.dataPlot.setPen((200,200,100))
        
        self.xValues = np.arange(self.dataSource.resultsLength)
        
        pw.setLabel('left', 'Displacement', units='px')
        pw.setLabel('bottom', 'Index', units='#')
        pw.setXRange(0, 200)
        pw.setYRange(0, 10)
        
        pw.setAutoVisible(y=True)

    def updatePlot(self):
        if "displacement_mp" in self.dataSource.resultsDataFrame.columns:
            self.xValues = np.arange(self.dataSource.resultsLength)
            yValues = self.dataSource.getOrCreateResultColumn("displacement_mp")
            self.dataPlot.setData(x=self.xValues, y=yValues)
        

class ODMStudioMainWindow(qt.QMainWindow):

    filesDropped = q.pyqtSignal(list)

    @property
    def dataSource(self):
        return self.__dataSource

    def __init__(self,parent=None):
        qt.QMainWindow.__init__(self,parent)
        
        self.__dataSource = lib.DataSource()

        self.setWindowTitle("ODM Studio")
        self.resize(800,600)
        self.setAcceptDrops(True)

        area = dock.DockArea()
        self.dockArea = area
        self.setCentralWidget(area)


        self.displacementPlot = DisplacementPlotWidget(self.dataSource, parent=self)
        self.fileOpener = FileOpener(self.dataSource, parent=self)
        self.intensityProfilePlot = IntensityProfilePlotWidget(self.dataSource, parent=self)

        movingFeature = lib.TrackableFeature("moving feature", "mp", self.dataSource)
        referenceFeature = lib.TrackableFeature("reference feature", "ref", self.dataSource)        
        
        self.movingFeatureWidget = TrackableFeatureWidget(movingFeature, parent=self)
        self.referenceFeatureWidget = TrackableFeatureWidget(referenceFeature, parent=self)
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
        
        self.dataSource.sourcePathChanged.connect(self.setWindowTitle)
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