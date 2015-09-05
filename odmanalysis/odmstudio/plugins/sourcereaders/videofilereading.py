from odmanalysis.odmstudio import odmstudio_lib as lib
from odmanalysis.odmstudio import odmstudio_framework as framework
import pandas as pd
import numpy as np
import cv2
import PyQt4.QtCore as q
import PyQt4.QtGui as qt
import pyqtgraph as pg
from pyqt2waybinding import Observer
import moviepy.editor

@framework.RegisterSourceReader("Video files", extensions=('avi','mpg'), maxNumberOfFiles=1)
class VideoReader(lib.SourceReader):

    currentFrameIndexChanged = q.pyqtSignal(int)

    @property
    def aoiSlices(self):
        return (slice(self._aoi[0],self._aoi[0] + self._aoi[2]), slice(self._aoi[1],self._aoi[1] + self._aoi[3]))
    
    @property
    def currentFrameIndex(self):
        return self.__currentFrameIndex

    @currentFrameIndex.setter
    def currentFrameIndex(self,value):
        if (self.__currentFrameIndex != value):
            self.__currentFrameIndex = value
            self.currentFrameIndexChanged.emit(value)

    
    @property
    def currentFrameTime(self):
        return self.currentFrameIndex / self.frameRate

    @property
    def frameRate(self):
        value = self.__clip.fps
        return value

    @property
    def frameCount(self):
        value = int(self.__clip.duration * self.frameRate)
        return value

    @property
    def frameSize(self):
        value = (self.__clip.w, self.__clip.h)
        return value

    @property
    def roi(self):
        return self.__roi

    @property
    def imageItem(self):
        return self.__imageItem

    @property
    def currentFrame(self):
        return self.__currentFrame

    @property
    def currentRegionOfInterest(self):
        return self.__roi.getArrayRegion(self.__currentFrame,self.__imageItem)

    def __init__(self,dataSource):
        lib.SourceReader.__init__(self,dataSource)
        
        self._aoi = (0,0,100,100) #x_left,y_top,width,height
        self.summingAxis = 0
        self.__currentFrameIndex = -1
        self.__roi = pg.ROI((0,0))
        self.__imageItem = pg.ImageItem()
        self.__currentFrame = None
        self.__clip = None

    def _initializeVideoCapture(self):
        self.__clip = moviepy.editor.VideoFileClip(self.sourcePath)
        
        self.currentFrameIndex = 0
        self.__roi.setSize([s/5.0 for s in self.frameSize])

    def _closeVideoCapture(self):
        pass


    def grabFrameAtIndex(self):
        if self.__clip is not None:
            clip = self.__clip
            self.__currentFrame = clip.get_frame(self.currentFrameTime)
            
            self.imageItem.setImage(self.__currentFrame)

    def read(self):
        
        path = self.sourcePath
        super(VideoReader, self).read()


        frameCount = self.frameCount
        frameRate = self.frameRate
        frameSize = self.frameSize
        
        np.arange(frameCount)/frameRate

        framesRead = 0
        intensityProfiles = []
        timeSteps = np.arange(frameCount)/frameRate
        
        for i,frame in enumerate(self.__clip.iter_frames()):
            self.__currentFrame = frame

            line = self.currentRegionOfInterest.sum(axis=2).sum(axis=1)
            
            intensityProfiles.append(line)

            framesRead = i+1
            self.dataSource.setSourceDataFrame(pd.DataFrame(data={'intensityProfile': intensityProfiles, 'timeStep': timeSteps[0:framesRead]}))

            self._setProgress((framesRead*100)/frameCount)
            self._setStatusMessage("%i frames read" % framesRead)

        self._setStatusMessage("file loaded")
        self._setProgress(100)
    
    

        
@framework.RegisterWidgetFor(VideoReader)
class VideoReaderDialog(qt.QDialog):
    def __init__(self, videoReader, parent=None):
        qt.QDialog.__init__(self,parent)

        assert isinstance(videoReader,VideoReader)
        self.videoReader = videoReader

        layout = qt.QVBoxLayout()        
        self.setLayout(layout)
        
        hLayout = qt.QHBoxLayout()
        
        self.frameSlider = qt.QSlider(q.Qt.Horizontal)
        self.frameSlider.setTickPosition(qt.QSlider.TicksBothSides)
        self.frameSlider.setTickInterval(1)
        
        self.frameSpinBox = qt.QSpinBox()
        
        hLayout.addWidget(self.frameSpinBox)
        hLayout.addWidget(self.frameSlider)

        layout.addLayout(hLayout)


        self.imagePlotWidget = pg.PlotWidget(self)
        imageItem = self.videoReader.imageItem
        self.imagePlotWidget.addItem(imageItem)
        self.imagePlotWidget.setAspectLocked(True)
        self.imagePlotWidget
        
        # Custom ROI for selecting an image region
        roi = self.videoReader.roi
        roi.addScaleHandle([0.5, 1], [0.5, 0])
        roi.addRotateHandle([0, 0.5], [0.5, 0.5])
        roi.addScaleHandle([1, 0.5], [0, 0.5])
        roi.addScaleHandle([0.5, 0], [0.5, 1])
        roi.addScaleHandle([0, 0], [1, 1])
        roi.addScaleHandle([0, 1], [1, 0])
        roi.addScaleHandle([1, 1], [0, 0])
        roi.addScaleHandle([1, 0], [0, 1])
        roi.addRotateHandle([1,0.3], [0.5,0.5])
        self.imagePlotWidget.addItem(roi)
        roi.setZValue(10)  # make sure ROI is drawn above image

        ipw = self.imagePlotWidget
        
        ipw.setAutoVisible(y=True)

        layout.addWidget(ipw)

        self.roiVerticalSumPlotWidget = pg.PlotWidget()
        self.roiVerticalSumPlot = self.roiVerticalSumPlotWidget.plot()
        self.roiVerticalSumPlot.setPen((200,200,100))


        layout.addWidget(self.roiVerticalSumPlotWidget)

        # OK and Cancel buttons
        buttons = qt.QDialogButtonBox(
            qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel,
            q.Qt.Horizontal, self)
        buttons.accepted.connect(self.videoReader.read)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)


        #create bindings
        self.frameObserver = Observer()
        self.frameObserver.bindToProperty(self.frameSlider,"value")
        self.frameObserver.bindToProperty(self.frameSpinBox,"value")
        self.frameObserver.bindToProperty(self.videoReader,"currentFrameIndex")
        
        self.videoReader.currentFrameIndexChanged.connect(self._showCurrentFrame)
        self.videoReader.roi.sigRegionChanged.connect(self.updateRoiPlots)

        self.videoReader._initializeVideoCapture()
        self.frameSlider.setMaximum(self.videoReader.frameCount)
        self.frameSpinBox.setMaximum(self.videoReader.frameCount)

    def _showCurrentFrame(self):
        self.videoReader.grabFrameAtIndex()
        self.updateRoiPlots()

    def updateRoiPlots(self):
        selected = self.videoReader.currentRegionOfInterest
        self.roiVerticalSumPlot.setData(x=np.arange(selected.shape[0]),y=selected.sum(axis=2).sum(axis=1),clear=True)
        

