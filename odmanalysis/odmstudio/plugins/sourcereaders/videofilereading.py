from odmanalysis.odmstudio import odmstudio_lib as lib
from odmanalysis.odmstudio import odmstudio_framework as framework
import pandas as pd
import numpy as np
import cv2

@framework.RegisterSourceReader("Video files", extensions=('avi','mpg'), maxNumberOfFiles=1)
class VideoReader(lib.SourceReader):

    def __init__(self,dataSource):
        lib.SourceReader.__init__(self,dataSource)
        
        self._aoi = (0,0,100,100) #x_left,y_top,width,height
        self.summingAxis = 0

    def read(self, paths):
        
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
            
            intensityProfiles.append(line)

            framesRead += 1
            self.dataSource.setSourceDataFrame(pd.DataFrame(data={'intensityProfile': intensityProfiles, 'timeStep': timeSteps[0:framesRead]}))

            self._setProgress((framesRead*100)/frameCount)
            self._setStatusMessage("%i frames read" % framesRead)

        
        
        self._setStatusMessage("file loaded")
        self._setProgress(100)
    
    

    @property
    def aoiSlices(self):
        return (slice(self._aoi[0],self._aoi[0] + self._aoi[2]), slice(self._aoi[1],self._aoi[1] + self._aoi[3]))
        