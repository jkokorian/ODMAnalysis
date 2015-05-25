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
    currentFrameChanged = q.pyqtSignal(np.ndarray)

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



    def __init__(self,dataSource):
        lib.SourceReader.__init__(self,dataSource)
        
        self._aoi = (0,0,100,100) #x_left,y_top,width,height
        self.summingAxis = 0
        self.__currentFrameIndex = -1

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

        self.imagePlot = pg.PlotWidget(self)
        self.imageItem = pg.ImageItem()
        self.imagePlot.addItem(self.imageItem)

        self.setLayout(layout)


        #create bindings
        self.frameObserver = Observer()
        self.frameObserver.bindToProperty(self.frameSlider,"value")
        self.frameObserver.bindToProperty(self.frameSpinBox,"value")
        self.frameObserver.bindToProperty(self.videoReader,"currentFrameIndex")

        