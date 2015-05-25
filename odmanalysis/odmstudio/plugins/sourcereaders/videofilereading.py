from odmanalysis.odmstudio import odmstudio_lib as lib
from odmanalysis.odmstudio import odmstudio_framework as framework
import pandas as pd
import numpy as np
import cv2
import PyQt4.QtCore as q
import PyQt4.QtGui as qt
import pyqtgraph as pg
from pyqt2waybinding import Observer

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
    def frameRate(self):
        value = self.__videoCapture.get(5)
        return value

    @property
    def frameCount(self):
        value = int(self.__videoCapture.get(7))
        return value

    @property
    def frameSize(self):
        value = (self.__videoCapture.get(3), self.__videoCapture.get(4))
        return value

    def __init__(self,dataSource):
        lib.SourceReader.__init__(self,dataSource)
        
        self._aoi = (0,0,100,100) #x_left,y_top,width,height
        self.summingAxis = 0
        self.__currentFrameIndex = -1
        

    def _initializeVideoCapture(self):
        self.__videoCapture = cv2.VideoCapture(self.sourcePath)
        
        self.currentFrameIndex = 0

    def _closeVideoCapture(self):
        self.__videoCapture.release()


    def readCurrentFrame(self):
        if self.__videoCapture.isOpened():
            vid = self.__videoCapture
            vid.set(cv2.cv.CV_CAP_PROP_POS_FRAMES,self.currentFrameIndex)
            retval, im = vid.read()
            return im
            
        else:
            return None

    def read(self):
        
        path = self.sourcePath
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
            
            intensityProfiles.append(line)

            framesRead += 1
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
        self.__currentFrame = None

        layout = qt.QVBoxLayout()        
        self.setLayout(layout)
        
        hLayout = qt.QHBoxLayout()
        layout.addLayout(hLayout)
        
        self.frameSlider = qt.QSlider(q.Qt.Horizontal)
        self.frameSlider.setTickPosition(qt.QSlider.TicksBothSides)
        self.frameSlider.setTickInterval(1)
        
        self.frameSpinBox = qt.QSpinBox()
        
        hLayout.addWidget(self.frameSpinBox)
        hLayout.addWidget(self.frameSlider)

        self.imagePlotWidget = pg.PlotWidget(self)
        self.imageItem = pg.ImageItem()
        self.imagePlotWidget.addItem(self.imageItem)
        
        # Custom ROI for selecting an image region
        roi = pg.ROI([-8, 14], [6, 5])
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
        self.roi = roi

        ipw = self.imagePlotWidget
        
        ipw.setAutoVisible(y=True)

        layout.addWidget(ipw)

        self.roiVerticalSumPlotWidget = pg.PlotWidget(self)
        self.roiVerticalSumPlotItem = pg.PlotItem()
        self.roiVerticalSumPlotWidget.addItem(self.roiVerticalSumPlotItem)


        layout.addWidget(self.roiVerticalSumPlotWidget)

        # OK and Cancel buttons
        buttons = qt.QDialogButtonBox(
            qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel,
            q.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)


        #create bindings
        self.frameObserver = Observer()
        self.frameObserver.bindToProperty(self.frameSlider,"value")
        self.frameObserver.bindToProperty(self.frameSpinBox,"value")
        self.frameObserver.bindToProperty(self.videoReader,"currentFrameIndex")
        
        self.videoReader.currentFrameIndexChanged.connect(self._showCurrentFrame)
        self.roi.sigRegionChanged.connect(self.updateRoiPlots)

        self.videoReader._initializeVideoCapture()
        self.frameSlider.setMaximum(self.videoReader.frameCount)
        self.frameSpinBox.setMaximum(self.videoReader.frameCount)

    def _showCurrentFrame(self):
        frame = self.videoReader.readCurrentFrame()
        self.__currentFrame = frame
        self.imageItem.setImage(frame)
        self.updateRoiPlots()

    def updateRoiPlots(self):
        selected = self.roi.getArrayRegion(self.__currentFrame,self.imageItem)
        self.roiVerticalSumPlotItem.plot(selected.sum(axis=2).sum(axis=1),clear=True)
        pass


