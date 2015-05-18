from odmanalysis.odmstudio import odmstudio_lib as lib
from odmanalysis.odmstudio import odmstudio_framework as fw
from odmanalysis.odmstudio.odmstudio_gui import PlotController
from PyQt4 import QtCore as q
from PyQt4 import QtGui as qt

@fw.RegisterFeatureTracker()
class FFTPhaseShiftTracker(lib.FeatureTracker):
    
    @classmethod
    def getDisplayName(cls):
        return "FFT phase shift"
    
    def __init__(self):
        lib.FeatureTracker.__init__(self)
        
    def findNextPosition(self, intensityProfile):
        """
        TODO: implement
        """
        return super(FFTTracker, self).findPosition(intensityProfile)


@fw.RegisterWidgetFor(FFTPhaseShiftTracker)
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