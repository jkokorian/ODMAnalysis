from odmanalysis.odmstudio import odmstudio_lib as lib
from odmanalysis.odmstudio import odmstudio_framework as fw
from odmanalysis.odmstudio.odmstudio_gui import PlotController
from odmanalysis.fitfunctions import ScaledSpline
from PyQt4 import QtGui as qt
from scipy.optimize import curve_fit
import numpy as np


@fw.RegisterFeatureTracker()
class SimpleSplineTracker(lib.FeatureTracker):
    @classmethod
    def getDisplayName(cls):
        return "Simple spline-fit"

    def __init__(self):
        lib.FeatureTracker.__init__(self)
        self.fitFunction = ScaledSpline()
        self.xValues = np.array([])

    def initialize(self,intensityProfile):
        valuesDict = self.fitFunction.estimateInitialParameters(intensityProfile,filter_sigma=1)
        self.p0 = valuesDict.values()
        self.xValues = np.arange(len(intensityProfile))
                    
    def findNextPosition(self,intensityProfile):
        popt,pcov = curve_fit(self.fitFunction, self.xValues[self.rangeSlice],intensityProfile[self.rangeSlice],self.p0,maxfev=10000)
        self.p0 = popt
        return self.fitFunction.getDisplacement(*popt)


        
        
        


@fw.RegisterFeatureTracker()
class CurveFitTracker(lib.FeatureTracker):

    @classmethod
    def getDisplayName(cls):
        return "Curve-fit"

    def __init__(self):
        lib.FeatureTracker.__init__(self)
        self.fitFunction = None     
        
        
    def findPosition(self,intensityProfile):
        #TODO: implement        
        return 0


@fw.RegisterWidgetFor(CurveFitTracker)
class CurveFitTrackerWidget(qt.QWidget,PlotController):


    def __init__(self,parent=None):
        qt.QWidget.__init__(self,parent)
        PlotController.__init__(self,parent)
        
        self._sourceIntensityProfiles = None
        
        layout = qt.QVBoxLayout()
        self.groupbox = qt.QGroupBox("Curve-fit settings")
        layout.addWidget(self.groupbox)
        self.setLayout(layout)
        

    def connectToPlotWidget(self, plotWidget):
        return super(CurveFitTrackerWidget, self).connectToPlotWidget(plotWidget)

    def disconnectPlotWidget(self):
        pass

