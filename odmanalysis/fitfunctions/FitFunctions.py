"""
    Copyright (C) 2014 Delft University of Technology, The Netherlands

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Created on Tue Aug 20 10:55:08 2013

@author: jkokorian
"""

import numpy as np

from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.ndimage.filters import gaussian_filter
from scipy import vectorize

class EstimatorDefinition(object):
    def __init__(self,id,promptMessage=None):
        self.id = id
        if not promptMessage:
            self.promptMessage = "Select coordinates for %s" % self.id
        else:
            self.promptMessage = promptMessage
        

class FitFunction(object):
    def __init__(self):
        pass
    
    """
    Calculates the initial parameter from several xy-value pairs.
    """
    def estimateInitialParameters(self,**estimatorValues):
        raise NotImplementedError("override this function")
    
    """
    Returns a function object of the fit-function.
    This function should have one independent variable and one parameter
    """
    def __call__(self,x,intensityProfile,peakCoordinates, lowerValleyCoordinates, upperValleyCoordinates, minBound,maxBound):
        raise NotImplementedError("override this method")
        
    """
    Returns the name of this fit function
    """
    def getName(self):
        raise NotImplementedError("override this method")
    
    """
    Returns a list of estimator definitions. The estimator id's should correspond to the parameter
    names of the estimateInitialParameters function.
    """
    def getEstimatorDefinitions(self):
        estimators = []
        estimators.append(EstimatorDefinition('peakCoordinates',"Select Peak"))
        estimators.append(EstimatorDefinition('lowerValleyCoordinates',"Select Lower Valley"))
        estimators.append(EstimatorDefinition('upperValleyCoordinates',"Select Upper Valley"))
        estimators.append(EstimatorDefinition('minBound',"Select Lower x Limit"))
        estimators.append(EstimatorDefinition('maxBound',"Select Upper x Limit"))
        return estimators


class DisplacementFitFunction(FitFunction):
    def __init__(self):
        super(DisplacementFitFunction,self).__init__()
    
    def getDisplacement(*parameters):
        raise NotImplementedError("override this method")

class BeamWidthFitFunction(FitFunction):
    def __init__(self):
        super(BeamWidthFitFunction,self).__init__()
    
    def getBeamWidth(*parameters):
        raise NotImplementedException("override this function")


class Gaussian(DisplacementFitFunction,BeamWidthFitFunction):
    def __init__(self):
        super(Gaussian,self).__init__()
    
    def estimateInitialParameters(self,intensityProfile,peakCoordinates, lowerValleyCoordinates, upperValleyCoordinates, minBound,maxBound):
        sigmaEst =  (upperValleyCoordinates[0]-lowerValleyCoordinates[0])/2       
        return {'mu' : peakCoordinates[0],
                'sigma' : sigmaEst,
                'A' : peakCoordinates[1]*sigmaEst,
                'a1': 0,
                'a0': (lowerValleyCoordinates[1]+upperValleyCoordinates[1])/2
                }
        
    def __call__(self,x,mu,sigma,A,a1,a0):
        return A*(1/(sigma * np.sqrt(2*np.pi)) * np.exp(-1/2 * ((x-mu)/sigma)**2)) + 0.003*a1*(x-mu) + a0
        
    
    def getName(self):
        return "Gaussian"
    
    def getDisplacement(self,mu,sigma,a1,a0,A):
        return mu
        
    def getBeamWidth(self,mu,sigma,a1,a0,A):
        return 2*sigma


class Harmonic(DisplacementFitFunction):
    def __init__(self):
        super(Harmonic,self).__init__()
     
    def __call__(self,x,x0,A,f,a1,a0):
        return A * np.cos(2.*np.pi*f*(x-x0)) + a1 * (1 + 0.0003*x) + a0
                  
    def estimateInitialParameters(self,intensityProfile,peakCoordinates, lowerValleyCoordinates, upperValleyCoordinates, minBound,maxBound):
        return {'x0': peakCoordinates[0],
                'A': (peakCoordinates[1]-lowerValleyCoordinates[1])/2,
                'f': 1/(upperValleyCoordinates[0] - lowerValleyCoordinates[0]),
                'a1': 0,
                'a0': (lowerValleyCoordinates[1]+upperValleyCoordinates[1])/2
                }
                 
    def getName(self):
        return "Harmonic"
        
    def getInitialParameters(self):
        return 0
    
    def getDisplacement(self,x0,A,f,a1,a0):
        return x0
	

class Merlijnian(DisplacementFitFunction, BeamWidthFitFunction):
    def __init__(self):
        super(Merlijnian,self).__init__()
    
    
    def __call__(self,x,a1,a2,a3,a4,a5,a6):
        return -(1/(a1+(x-a2)**2)+1/(a1+(x-a3)**2)) * a4 * (x-a5)**2 * (1. + 0.0003*x) + a6        
        
    def estimateInitialParameters(self,intensityProfile,peakCoordinates, lowerValleyCoordinates, upperValleyCoordinates, minBound,maxBound):
        return {'a1': np.sqrt(peakCoordinates[0]-lowerValleyCoordinates[0]),
                'a2': lowerValleyCoordinates[0],
                'a3': upperValleyCoordinates[0],
                'a4': peakCoordinates[1],
                'a5': peakCoordinates[0],
                'a6': peakCoordinates[1]
                }
         
    def getName(self):
        return "Inverted Double Lorentzian (Merlijn)"
        
    def getDisplacement(self,a1,a2,a3,a4,a5,a6):
        return (a3+a2)/2
        
    def getBeamWidth(self,a1,a2,a3,a4,a5,a6):
        return np.abs(a3-a2)

class Jaapian(DisplacementFitFunction, BeamWidthFitFunction):
    def __init__(self):
        super(Jaapian,self).__init__()
    
    def __call__(self,x,w,Gamma,contrast,x0,A,a0):
        def L(x,w=20,Gamma=5,contrast=1,x0=0):
            return (1-contrast)+contrast * (1-(Gamma**2)/4 * 1/((Gamma/2)**2 + (x - w/2 - x0)**2))*(1-(Gamma**2)/4 * 1/((Gamma/2)**2 + (x + w/2 - x0)**2))
        
        return A*L(x,w,Gamma,contrast,x0)+a0
        
    def estimateInitialParameters(self,intensityProfile,peakCoordinates, lowerValleyCoordinates, upperValleyCoordinates, minBound,maxBound):
        return {'w': upperValleyCoordinates[0] - lowerValleyCoordinates[0],
                'Gamma': 10,
                'contrast': 1,
                'x0': peakCoordinates[0],
                'A': peakCoordinates[1],
                'a0': lowerValleyCoordinates[1]
                }
         
    def getName(self):
        return "Inverted Double Lorentzian (Jaap)"
        
    def getDisplacement(self,w,Gamma,contrast,x0,A,a0):
        return x0

    def getBeamWidth(self,w,Gamma,contrast,x0,A,a0):
        return w


class DualHarmonic(DisplacementFitFunction):
    def __init__(self):
        super(DualHarmonic,self).__init__()
    
    def getName(self):
        return "Dual Harmonic"
    
    def __call__(self,x,x0,w,a1,a2,a0):
        return a1*np.cos(w*(x-x0)) + a2*np.cos(2*w*(x-x0)) + a0
    
    def estimateInitialParameters(self,intensityProfile,peakCoordinates,lowerValleyCoordinates,upperValleyCoordinates,minBound,maxBound):
        a0 = (minBound[1] + maxBound[1])/2
        a1 = (peakCoordinates[1]-a0)/2
        a2 = a1
        return {'x0': peakCoordinates[0],
                'w': np.pi*1/(upperValleyCoordinates[0]-lowerValleyCoordinates[0]),
                'a1': a1,
                'a2': a2,
                'a0': a0}
    
    def getDisplacement(self,x0,w,a1,a2,a0):
        return x0

class Spline(DisplacementFitFunction):
    def __init__(self):
        super(Spline,self).__init__()
        self.spline = None
        
    def getName(self):
        return "Spline"

    def __call__(self,x,x0):
        return self.spline(x-x0)
    
    def estimateInitialParameters(self,intensityProfile,**kwargs):
        xValues = np.arange(len(intensityProfile))
        yValues = gaussian_filter(intensityProfile,2)
        self.spline = InterpolatedUnivariateSpline(xValues, yValues)
        return {'x0': 0.0}
        
    def getDisplacement(self,x0):
        return x0
    
class ScaledSpline(DisplacementFitFunction):
    def __init__(self):
        super(ScaledSpline,self).__init__()
        self.spline = None
        
    def getName(self):
        return "Scaled Spline"

    def __call__(self,x,x0,A,a0):
        return A*self.spline(x-x0)+a0
    
    def estimateInitialParameters(self,intensityProfile,**kwargs):
        xValues = np.arange(len(intensityProfile))
        yValues = gaussian_filter(intensityProfile,2)
        self.spline = InterpolatedUnivariateSpline(xValues, yValues)
        return {'x0': 0.0,
                'A': 1.0,
                'a0': 0.0}
        
    def getDisplacement(self,x0,A,a0):
        return x0
        
    def getEstimatorDefinitions(self):
        estimators = []
        return estimators

class BoundedSpline(DisplacementFitFunction):
    def __init__(self):
        super(BoundedSpline,self).__init__()
        self.spline = None
        self.xmin = None
        self.xmax = None
        self.ymax = None
        self.ymin = None
        
    def getName(self):
        return "Bounded Spline"
    
    
    def __call__(self,x,x0,A,a0):
        
        @vectorize
        def boundedSpline(xValue):
            if (xValue < self.xmin):
                return self.ymin
            elif (xValue > self.xmax):
                return self.ymax
            else:
                return (A*self.spline(xValue-x0)+a0)
            #return (1.0 if xValue > self.xmin and xValue < self.xmax else np.NaN)
        
        return boundedSpline(x)
        
        
    def estimateInitialParameters(self,intensityProfile,splineMinBound,splineMaxBound,**kwargs):
        xmin = int(round(splineMinBound[0]))
        xmax = int(round(splineMaxBound[0])) 
        self.xmin = xmin
        self.xmax = xmax
        yValues = gaussian_filter(intensityProfile[xmin:xmax],2)        
        xValues = np.arange(xmin,xmax)
        self.spline = InterpolatedUnivariateSpline(xValues, yValues)
        
        self.ymin = self.spline(xmin)
        self.ymax = self.spline(xmax)
        return {'x0': 0.0,
                'A': 1.0,
                'a0': 0.0}
        
    def getDisplacement(self,x0,A,a0):
        return x0
        
    def getEstimatorDefinitions(self):
        estimators = []
        estimators.append(EstimatorDefinition("splineMinBound","lower bound of interesting part"))
        estimators.append(EstimatorDefinition("splineMaxBound","upper bound of interesting part"))
        return estimators
    
class Sinc(DisplacementFitFunction):
    def __init__(self):
        super(Sinc,self).__init__()
    
    def __call__(self,x,w,A,c,x0):
        def sinc(x):
            return A*np.sin(w*(x-x0))/(w*(x-x0)) + c

        
        return sinc(x)
            
        
    def estimateInitialParameters(self,intensityProfile,peakCoordinates, lowerValleyCoordinates, upperValleyCoordinates, minBound,maxBound):
        x0 = peakCoordinates[0]
        w = 2*np.pi * 1/(((upperValleyCoordinates[0]-x0) + (x0-lowerValleyCoordinates[0]))/2 * 4/3)
        c = (minBound[1]+maxBound[1])/2
        A = peakCoordinates[1] - c
        return {'x0': x0, 'w': w, 'c': c, 'A': A}
         
    def getName(self):
        return "Sinc"
        
    def getDisplacement(self,w,A,c,x0):
        return x0




def createFitFunctions():
    return [Merlijnian(),Gaussian(),Harmonic(),Jaapian(),Sinc(),DualHarmonic(),Spline(),ScaledSpline(),BoundedSpline()]

def createFitFunction(name):
    fitFunctionsDict = {ff.getName() : ff for ff in createFitFunctions()}
    return fitFunctionsDict[name]
    