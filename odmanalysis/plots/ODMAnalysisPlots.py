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

Created on Tue Dec 17 09:57:12 2013

@author: jkokorian
"""

from __future__ import division as _division
import numpy as _np
import os as _os
import matplotlib.pyplot as _plt
import matplotlib.dates as _mpld
from matplotlib import animation as _animation
from odmanalysis import stats as _ODMStats
from odmanalysis.ProgressReporting import BasicProgressReporter as _BasicProgressReporter
from threading import RLock


class ODMPlot(object):
    """
    Decorate methods that produce plots from a processed odm dataframe with this
    class to indicate for which kinds of data they should be returned by the PlotFactory.
    
    The decorator constructor allows several options to indicate for which kinds of
    data the plot is suitable.
    
    Functions that are decorated with this class should at least allow the following arguments
    
    args:
        df, pandas.DataFrame: The odm analysis dataframe
    
    kwargs:        
        measurementName, String: Name of the measurement
        nmPerPx, float: Number of nanometers per pixel
        figure, matplotlib.Figure: optional existing figure to use to create the plot
        axes, matplotlib.Axes: optional existing axes to use to create the plot
        **kwargs: The function should allow for other kwargs to be passed but not used.
    
    Usage
    -----
    
    To retrieve a list of all the functions that are decorated with @ODMPlot(), call
    the appropriate class method:
    
    >>> ODMPlot.getRegisteredPlotFunctions()
    
    
    """
    
    __odmPlots = []
    __lock = RLock()
    
    @classmethod
    def __addPlot(cls,odmPlot):
        with cls.__lock:
            cls.__odmPlots.append(odmPlot)
    
    @classmethod
    def getSuitablePlotFunctions(cls,df):
        return [odmPlot.plotFunction for odmPlot in cls.getSuitablePlotDefinitions(df)]
    
    @classmethod
    def getSuitablePlotDefinitions(cls,df):
        return [odmPlot for odmPlot in cls.__odmPlots if odmPlot.isSuitableFor(df)]
    
    @classmethod
    def getRegisteredPlotDefinitions(cls):
        return cls.__odmPlots[:]
    
    @classmethod
    def getRegisteredPlotFunctions(cls):
        return [odmPlot.plotFunction for odmPlot in cls.__odmPlots]
        
    def __init__(self,filename,requiresSingleCycle=False,requiresMultipleCycle=False,maxNumberOfCycles=200,requiresConstantVoltage=False,requiresVariableVoltage=False,requiresReference=False,suitability_check_functions = []):
        """
        Parameters
        ----------
        
        requiresSingleCycle: boolean, default False
            The plot should be created exclusively for dataframes containing only a single cycle.
        
        requiresMultipleCycle: boolean, default True
            The plot should be created exclusively for dataframes containing multiple cycles.
            
        maxNumberOfCycles: integer, default 200
            If 'multipleCycle'==True, this number indicates the maximum number of cycles
            the plot will still be created.
        
        requiresConstantVoltage: boolean, default False
            The plot should be created exclusively for dataframes where the actuator voltage is constant.
        
        requiresVariableVoltage: boolean, default False
            The plot should not be created for dataframes that have a constant voltage
        
        requiresReference: boolean, default False
            The plot should be created exclusivelyfor dataframes that have a reference
            
        suitability_check_functions: list or tuple of functions, default []
            Custom function with a single parameter accepting a dataframe to check
            whether the plot should be created.
        """
        self.filename = filename
        self.requiresSingleCycle = requiresSingleCycle
        self.requiresMultipleCycle = requiresMultipleCycle
        self.requiresConstantVoltage = requiresConstantVoltage
        self.requiresVariableVoltage = requiresVariableVoltage
        self.maxNumberOfCycles = maxNumberOfCycles
        self.requiresReference = requiresReference
        self.suitability_check_functions = suitability_check_functions
    
    def __call__(self,f):
        """
        Decorates the function.
        """
        self.plotFunction = f
        ODMPlot.__addPlot(self)
        return f
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return "<ODMPlot: self.plotFunction.func_name>"
    
    def isSuitableFor(self,df):
        """
        Checks whether the decorated ODMPlot function should be run for the target
        dataframe, based on the arguments passed to the ODMPlot decorator.
        """
        result = True
        if (self.requiresConstantVoltage and not hasConstantVoltage(df)):
            result = False
        if (self.requiresVariableVoltage and hasConstantVoltage(df)):
            result = False
        if (self.requiresSingleCycle and not hasSingleCycle(df)):
            result = False
        if (self.requiresMultipleCycle and not hasMultipleCycles(df)):
            result = False
        if (df.cycleNumber.max() > self.maxNumberOfCycles):
            result = False
        if (self.requiresReference and not hasReference(df)):
            result = False
        if (not all([check(df) for check in self.suitability_check_functions])):
            result = False
        
        return result
    
    def runAndSave(self,df,saveDir,**kwargs):
        """
        Runs the decorated ODMPlot function and saves the result by invoking
        the last return value the function returns.
        """
        result = self.plotFunction(df,**kwargs)
        savePath = _os.path.join(saveDir,self.filename)
        result[-1](savePath)
        
        
def hasSingleCycle(odmAnalysisDataFrame):
    return not hasMultipleCycles(odmAnalysisDataFrame)

def hasMultipleCycles(odmAnalysisDataFrame):
    return len(odmAnalysisDataFrame.cycleNumber.unique()) > 1

def hasReference(odmAnalysisDataFrame):
    return 'displacement_ref' in odmAnalysisDataFrame.columns

def hasConstantVoltage(odmAnalysisDataFrame):
    return len(odmAnalysisDataFrame.actuatorVoltage.unique()) == 1

@ODMPlot("chi-square.png", requiresVariableVoltage=True)
@_BasicProgressReporter(entryMessage="creating chi-square plots...")
def plotChiSquare(df, savePath=None, measurementName="", figure = None, axes = None, nmPerPx=1, **kwargs):
    if not figure:    
        figure = _plt.figure('Chi-Squared (%s)' % measurementName)
    if not axes:
        axes = _plt.subplot(111)
    
    axes.plot(df.actuatorVoltage,df.chiSquare_mp,label='moving peak')
    if (hasReference(df)):
        axes.plot(df.actuatorVoltage,df.chiSquare_ref,label='reference')
    
    axes.set_title('$\chi$-Squared')
    axes.set_ylabel("$\chi^2$")
    axes.set_xlabel("Actuator Voltage (V)")

    def save(path):
        figure.savefig(path,dpi=200)
    
    return figure,axes, save


@ODMPlot("Voltage-Displacement.png",requiresSingleCycle=True, requiresVariableVoltage=True)
@_BasicProgressReporter(entryMessage="creating voltage-displacement graphs for single cycle...")
def plotSingleCycleVoltageDisplacement(df, corrected=False, showReferenceValues=False, measurementName="", nmPerPx=1, figure = None, axes = None, **kwargs):
    #show voltage-displacement curve
    if not figure:    
        figure = _plt.figure('Voltage Displacement %s (%s)' % ("(corrected)" if corrected else "", measurementName))
    if not axes:
        axes = _plt.subplot(111)
    
    fwd=df[df.direction=='forward']
    bwd=df[df.direction=='backward']
    
    axes.set_ylabel("Displacement (px)")
    axes.set_xlabel("Actuator Voltage (V)")
    axes.plot(fwd.actuatorVoltage,fwd.displacement,label="forward")
    axes.plot(bwd.actuatorVoltage,bwd.displacement,label="backward")
    axes.legend()
    
    tx = axes.twinx()
    tx.set_ylabel('Displacement (nm)')
    tx.set_ylim(nmPerPx * px for px in axes.get_ylim())

    def save(path):
        figure.savefig(path,dpi=200)
    
    return figure,axes, save

@ODMPlot("Voltage-Displacement (first cycle).png", 
         requiresMultipleCycle=True,
         maxNumberOfCycles=_np.infty,
         requiresVariableVoltage=True)
@_BasicProgressReporter(entryMessage="Creating voltage-displacement graph of first cycle")
def plotFirstCycleVoltageDisplacement(df, measurementName="", nmPerPx=1, figure = None, axes = None, **kwargs):
    return plotSingleCycleVoltageDisplacement(df[df.cycleNumber==1],measurementName=measurementName,nmPerPx=nmPerPx,figure=figure,axes=axes, **kwargs)

@ODMPlot("Voltage-Displacement (last cycle).png",
         requiresMultipleCycle=True,
         requiresVariableVoltage=True,
         maxNumberOfCycles=_np.infty)
@_BasicProgressReporter(entryMessage="Creating voltage-displacement graph of last cycle")
def plotLastCycleVoltageDisplacement(df, measurementName="", nmPerPx=1, figure = None, axes = None, **kwargs):
    return plotSingleCycleVoltageDisplacement(df[df.cycleNumber==df.cycleNumber.max()],measurementName=measurementName,nmPerPx=nmPerPx,figure=figure,axes=axes, **kwargs)


@ODMPlot("Voltage-Displacement (all cycles).png",
         maxNumberOfCycles=200,
         requiresMultipleCycle=True,
         requiresVariableVoltage=True)
@_BasicProgressReporter(entryMessage="Creating voltage-displacment graphs for multiple cycles...")
def plotMultiCycleVoltageDisplacement(df, measurementName="", nmPerPx=1, figure=None, axes=None, **kwargs):
    if not figure:    
        figure = _plt.figure('Multiple cycles (%s)' % measurementName)
    if not axes:
        axes = _plt.subplot(111)
    axes.set_ylabel("Displacement (px)")
    axes.set_xlabel("Actuator Voltage (V)")
    
    for cycleNumber in set(df.cycleNumber):
        dfFwdCycle = df[(df.cycleNumber == cycleNumber) & (df.direction == 'forward')]
        dfBwdCycle = df[(df.cycleNumber == cycleNumber) & (df.direction == 'backward')]
               
        forwardPlot, = axes.plot(dfFwdCycle.actuatorVoltage,dfFwdCycle.displacement,'b-')
        backwardPlot, = axes.plot(dfBwdCycle.actuatorVoltage,dfBwdCycle.displacement,'g-')
    
    
    axes.legend([forwardPlot,backwardPlot],['forward','backward'])
    
    tx = axes.twinx()
    tx.set_ylabel('Displacement (nm)')
    tx.set_ylim(nmPerPx * px for px in axes.get_ylim())
    
    def save(path):
        figure.savefig(path,dpi=200)
    
    return figure,axes, save
    

@ODMPlot("Voltage-Displacement.mp4",
         requiresMultipleCycle=True,
         requiresVariableVoltage=True,
         maxNumberOfCycles=_np.infty)
@_BasicProgressReporter(entryMessage="Creating multiple cycle voltage-displacement animation...")
def animateMultiCycleVoltageDisplacement(df, measurementName="", nmPerPx=1, figure=None, axes=None, dpi=200, progressReporter=None, **kwargs):
    """
    Creates an animation of the voltage displacement curves of all the cycles of a 
    multiple-cycle measurement. Each cycle is shown in a single frame, at 10 frames
    per second.
    
    System requirements
    -------------------
    
    This function uses the matplotlib animation package. To render the animation, ffmpeg
    should be installed on your system. For more information on ffmpeg, see: http://www.ffmpeg.org/
    """
    
    numberOfCycles = int(df.cycleNumber.max())
    if (progressReporter):
        progressReporter.message("rendering %i frames..." % numberOfCycles)

    #create dummy axis and plot to determine xlim and ylim
    df1 = df[df.cycleNumber == numberOfCycles//2]
    _plt.figure()
    axDummy = _plt.axes()
    axDummy.plot(df1.actuatorVoltage,df1.displacement)
    
    fig = _plt.figure('test')
    ax = _plt.axes(xlim=axDummy.get_xlim(), ylim=axDummy.get_ylim())
    fwdline, = ax.plot([], [], 'b')
    bwdline, = ax.plot([], [], 'g')
    text = ax.set_title("")
    
    # initialization function: plot the background of each frame
    def init_frame():
        fwdline.set_data([], [])
        bwdline.set_data([], [])
        text.set_text("")
        return fwdline,bwdline,text
    
    
    # animation function.  This is called sequentially
    def render_frame(i_frame):
        if (progressReporter):        
            progressReporter.progress((i_frame+1)/numberOfCycles * 100)
        dfc = df[df.cycleNumber == i_frame+1]
        fwd = dfc[dfc.direction == "forward"]
        bwd = dfc[dfc.direction == "backward"]
        fwdline.set_data(fwd.actuatorVoltage, fwd.displacement)
        bwdline.set_data(bwd.actuatorVoltage, bwd.displacement)
        text.set_text("cycle %i" % (i_frame+1))
        return fwdline,bwdline,text,
    
    # call the animator.  blit=True means only re-draw the parts that have changed.
    
    anim = _animation.FuncAnimation(fig, render_frame, init_func=init_frame,
                                   frames=numberOfCycles, interval=20, blit=True)
    
    # save the animation as an mp4.  This requires ffmpeg or mencoder to be
    # installed.  The extra_args ensure that the x264 codec is used, so that
    # the video can be embedded in html5.  You may need to adjust this for
    # your system: for more information, see
    # http://matplotlib.sourceforge.net/api/animation_api.html
    #progressReporter.message("Creating movie...")
    def save(path):    
        anim.save(path, fps=5, extra_args=['-vcodec', 'libx264'],dpi=dpi)
    
    
    return anim, save

@ODMPlot("Voltage-Displacement (mean).png",
         requiresMultipleCycle=True,
         requiresVariableVoltage=True)
@_BasicProgressReporter(entryMessage="Creating multiple cycle average graph...")
def plotMultiCycleMeanVoltageDisplacement(df, measurementName="", nmPerPx=1, figure=None, axes=None, **kwargs):
    if not figure:
        figure = _plt.figure('Multiple cycle average (%s)' % measurementName)
    if not axes:
        axes = _plt.subplot(111)
    axes.set_ylabel("Displacement (px)")
    axes.set_xlabel("Actuator Voltage (V)")
    
    grouped = df.groupby(['direction','actuatorVoltage'])['displacement']
    dfMean = grouped.agg({'displacement': _np.mean})
    dfMean.displacement['forward'].plot(ax=axes,label="forward")
    dfMean.displacement['backward'].plot(ax=axes,label="backward")
    
    axes.legend()        
    
    tx = axes.twinx()
    tx.set_ylabel('Displacement (nm)')
    tx.set_ylim(nmPerPx * px for px in axes.get_ylim())
    
    def save(path):
        figure.savefig(path,dpi=200)
    
    return figure,axes, save

@_BasicProgressReporter(entryMessage="Creating intensity profile plots...")
def plotIntensityProfiles(dfRaw,movingPeakFitSettings,referencePeakFitSettings,numberOfProfiles=10,measurementName="", nmPerPx=1, figure=None, axes=None, **kwargs):
    if not figure:
        figure = _plt.figure('Intensity Profiles (%s)' % measurementName)
    if not axes:
        axes = _plt.subplot(111)
    axes.set_xlabel('x (px)')
    axes.set_ylabel('Intensity (arb. units)')
    
    for i in range(0,len(dfRaw.intensityProfile),len(dfRaw.intensityProfile)//numberOfProfiles):
        
        xValues_mp = _np.arange(movingPeakFitSettings.xminBound,movingPeakFitSettings.xmaxBound)
        
        _plt.plot(dfRaw.intensityProfile.iloc[i],'b')
        _plt.plot(xValues_mp,movingPeakFitSettings.fitFunction(xValues_mp,*dfRaw.curveFitResult_mp.iloc[i].popt),'r--')
        
        if referencePeakFitSettings:
            xValues_ref = _np.arange(referencePeakFitSettings.xminBound,referencePeakFitSettings.xmaxBound)                
            _plt.plot(xValues_ref,referencePeakFitSettings.fitFunction(xValues_ref,*dfRaw.curveFitResult_ref.iloc[i].popt),'g--')
    
    ty = axes.twiny()
    ty.set_xlabel('x ($\mu$m)')
    ty.set_xlim(nmPerPx / 1000 * px for px in axes.get_xlim())
    
    def save(path):
        figure.savefig(path,dpi=200)
    
    return figure,axes, save

@ODMPlot("Position Histogram differential.png",
         requiresConstantVoltage=True,
         requiresReference=True)
def plotConstantDisplacementHistogramDiff(df, measurementName="", nmPerPx=1, figure=None, axes=None, **kwargs):
    return plotConstantDisplacementHistogram(df,source='diff', measurementName=measurementName, nmPerPx=nmPerPx, figure=figure, axes=axes, **kwargs)
    
    
@ODMPlot("Position Histogram moving peak.png",
         requiresConstantVoltage=True)
def plotConstantDisplacementHistogramMoving(df, measurementName="", nmPerPx=1, figure=None, axes=None, **kwargs):
    return plotConstantDisplacementHistogram(df,source='mp', measurementName=measurementName, nmPerPx=nmPerPx, figure=figure, axes=axes, **kwargs)
    
@ODMPlot("Position Histogram reference peak.png",
         requiresConstantVoltage=True,
         requiresReference=True)
def plotConstantDisplacementHistogramRef(df, measurementName="", nmPerPx=1, figure=None, axes=None, **kwargs):
    return plotConstantDisplacementHistogram(df,source='ref', measurementName=measurementName, nmPerPx=nmPerPx, figure=figure, axes=axes, **kwargs)
    
    
@_BasicProgressReporter(entryMessage="Creating histogram for constant displacement...")
def plotConstantDisplacementHistogram(df,source='diff', nbins=None, measurementName="", nmPerPx=1, figure=None, axes=None, **kwargs):
    titlesDict = {'diff': 'differential','mp': 'moving peak', 'ref': 'reference peak'}
    
    if not figure:    
        figure = _plt.figure('Position histogram: %s (%s)' % (titlesDict[source], measurementName))
    if not axes:
        axes = _plt.subplot(111)
    histogramKwargs = {'facecolor':'green', 'alpha':0.5,'normed': True}
    
    if (source == 'diff'):
        displacementValues = df.displacement
        
    elif (source == 'mp'):
        displacementValues = df.displacement_mp
        
    elif (source == 'ref'):
        displacementValues = df.displacement_ref
    
    if not nbins:
        nbins = int(round(_np.sqrt(len(displacementValues))))
    
    _plt.hist(displacementValues,bins=nbins,**histogramKwargs)
    
    sd = _ODMStats.makeStatsDescriptionDict(displacementValues * nmPerPx)
    peakDistanceToEdge = [abs(sd['mean']-x*nmPerPx) for x in axes.get_xlim()]
    xtext = 0.1 if peakDistanceToEdge[0] > peakDistanceToEdge[1] else 0.7
        
    _plt.text(xtext,0.7,_ODMStats.printStatsDescriptionDict(sd),transform=axes.transAxes)
    _plt.xlabel('position (px)')
    ty = axes.twiny()
    ty.set_xlabel('position (nm)')
    ty.set_xlim(nmPerPx * px for px in axes.get_xlim())

    
    def save(path):
        figure.savefig(path,dpi=200)
    
    return figure, axes, save


@ODMPlot("Timestamp-Displacement reference peak.png",
         requiresConstantVoltage=True, 
         requiresReference=True)
def plotDisplacementVersusTimestampRef(df, measurementName="", nmPerPx=1, figure=None, axes=None, **kwargs):        
    return plotDisplacementVersusTimestamp(df,sources='ref', measurementName=measurementName, nmPerPx=nmPerPx, figure=figure, axes=axes, **kwargs)
    
@ODMPlot("Timestamp-Displacement moving peak.png",
         requiresConstantVoltage=True, 
         requiresReference=False)
def plotDisplacementVersusTimestampMoving(df, measurementName="", nmPerPx=1, figure=None, axes=None, **kwargs):        
    return plotDisplacementVersusTimestamp(df,sources='mp', measurementName=measurementName, nmPerPx=nmPerPx, figure=figure, axes=axes, **kwargs)
    
@ODMPlot("Timestamp-Displacement differential.png",
         requiresConstantVoltage=True, 
         requiresReference=True)
def plotDisplacementVersusTimestampDiff(df, measurementName="", nmPerPx=1, figure=None, axes=None, **kwargs):        
    return plotDisplacementVersusTimestamp(df,sources='diff', measurementName=measurementName, nmPerPx=nmPerPx, figure=figure, axes=axes, **kwargs)
    
@_BasicProgressReporter(entryMessage="Creating timestamp versus displacement plot...")
def plotDisplacementVersusTimestamp(df,sources='diff', measurementName="", nmPerPx=1, figure=None, axes=None, **kwargs):        
    sources = sources.split(',')
    
    titlesDict = {'diff': 'differential','mp': 'moving peak', 'ref': 'reference peak'}
    title = ', '.join(titlesDict[s] for s in sources)
    if not figure:    
        figure = _plt.figure('Position-Time %s (%s)' % (title,measurementName))
    if not axes:
        axes = _plt.subplot(111)
    
    
    times = _mpld.date2num(df.index)
    times = times-times[0]
    alpha = 1 if len(sources) == 1 else 0.5
    for source in sources:
        if (source=='diff'):
            displacementValues = df.displacement
        elif (source=='mp'):
            displacementValues = df.displacement_mp
        elif (source=='ref'):
            displacementValues = df.displacement_ref
                
        axes.plot(times,displacementValues,alpha=alpha,label=titlesDict[source])
        
    axes.set_xlabel('Time (s)')
    axes.set_ylabel('Position (px)')
    
    if (len(sources)>1):
        axes.legend()
    
    tx = axes.twinx()
    tx.set_ylabel('Position (nm)')
    tx.set_ylim(nmPerPx * px for px in axes.get_ylim())
    
    def save(path):
        figure.savefig(path,dpi=200)
    
    return figure, axes, save
    
