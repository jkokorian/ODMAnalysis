# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 09:57:12 2013

@author: jkokorian
"""

from __future__ import division as _division
import numpy as _np
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
    """
    
    __odmPlots = []
    __lock = RLock()
    
    @classmethod
    def __addPlot(cls,odmPlot):
        with cls.__lock:
            cls.__odmPlots.append(odmPlot)
    
    @classmethod
    def getSuitablePlotFunctions(cls,df):
        return [odmPlot.plotFunction for odmPlot in cls.__odmPlots if odmPlot.isSuitableFor(df)]
    
    def __init__(self,singleCycle=True,multipleCycle=True,maxNumberOfCycles=200,constantVoltage=False,suitability_check_functions = []):
        """
        Parameters
        ----------
        
        singleCycle: boolean, default True
            The plot should be created for dataframes containing only a single cycle.
        
        multipleCycle: boolean, default True
            The plot should be created for dataframes containing multiple cycles.
            
        maxNumberOfCycles: integer, default 200
            If 'multipleCycle'==True, this number indicates the maximum number of cycles
            the plot will still be created.
        
        constantActuatorVoltage: boolean, default False
            The plot should be created for dataframes where the actuator voltage is constant.
            
        suitability_check_functions: list or tuple of functions, default []
            Custom function with a single parameter accepting a dataframe to check
            whether the plot should be created.
        """
        self.singleCycle = singleCycle
        self.multipleCycle = multipleCycle
        self.constantVoltage = constantVoltage
        self.maxNumberOfCycles = maxNumberOfCycles
        self.suitability_check_functions = suitability_check_functions
    
    def __call__(self,f):
        
        self.plotFunction = f
        ODMPlot.__addPlot(self)
        def wrapped_f(*args,**kwargs):
            f(*args,**kwargs)
        
        wrapped_f.func_name = f.func_name
        return wrapped_f
        
    def isSuitableFor(self,df):
        result = True        
        if (hasConstantVoltage(df) and not self.constantVoltage):
            result = False
        elif (hasSingleCycle(df) and not self.singleCycle):
            result = False
        elif (hasMultipleCycles(df) and not self.multipleCycle):
            result = False
        elif (df.cycleNumber.max() > self.maxNumberOfCycles):
            result = False
        elif (not all([check(df) for check in self.suitability_check_functions])):
            result = False
        
        return result
        
        
def hasSingleCycle(odmAnalysisDataFrame):
    return not hasMultipleCycles(odmAnalysisDataFrame)

def hasMultipleCycles(odmAnalysisDataFrame):
    return len(odmAnalysisDataFrame.cycleNumber.unique()) > 1

def hasReference(odmAnalysisDataFrame):
    return 'displacement_ref' in odmAnalysisDataFrame.columns

def hasConstantVoltage(odmAnalysisDataFrame):
    return len(odmAnalysisDataFrame.actuatorVoltage.unique()) == 1

@ODMPlot(maxNumberOfCycles=100)
@_BasicProgressReporter(entryMessage="creating chi-square plots...")
def plotChiSquare(df, filename=None, measurementName="", figure = None, axes = None, nmPerPx=1):
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

    if (filename):
        figure.savefig(filename,dpi=200)
    
    return figure,axes


@ODMPlot(multipleCycle=False)
@_BasicProgressReporter(entryMessage="creating voltage-displacement graphs for single cycle...")
def plotSingleCycleVoltageDisplacement(df, corrected=False, showReferenceValues=False, filename=None, measurementName="", nmPerPx=1, figure = None, axes = None):
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

    if (filename):
        figure.savefig(filename,dpi=200)
    
    return figure,axes

@ODMPlot(singleCycle=False,multipleCycle=True,maxNumberOfCycles=_np.infty)
@_BasicProgressReporter(entryMessage="Creating voltage-displacement graph of first cycle")
def plotFirstCycleVoltageDisplacement(df, corrected=False, showReferenceValues=False, filename=None, measurementName="", nmPerPx=1, figure = None, axes = None):
    return plotSingleCycleVoltageDisplacement(df[df.cycleNumber==1],corrected=corrected,showReferenceValues==showReferenceValues,filename=filename,measurementName=measurementName,nmPerPx=nmPerPx,figure=figure,axes=axes)

@ODMPlot(singleCycle=False,multipleCycle=True,maxNumberOfCycles=_np.infty)
@_BasicProgressReporter(entryMessage="Creating voltage-displacement graph of first cycle")
def plotLastCycleVoltageDisplacement(df, corrected=False, showReferenceValues=False, filename=None, measurementName="", nmPerPx=1, figure = None, axes = None):
    return plotSingleCycleVoltageDisplacement(df[df.cycleNumber==df.cycleNumber.max()],corrected=corrected,showReferenceValues==showReferenceValues,filename=filename,measurementName=measurementName,nmPerPx=nmPerPx,figure=figure,axes=axes)


@ODMPlot(singleCycle=False,maxNumberOfCycles=200)
@_BasicProgressReporter(entryMessage="Creating voltage-displacment graphs for multiple cycles...")
def plotMultiCycleVoltageDisplacement(df, corrected=False, showReferenceValues=False, filename=None, measurementName="", nmPerPx=1, figure=None, axes=None):
    if not figure:    
        figure = _plt.figure('Multiple cycles %s (%s)' % ("(corrected)" if corrected else "", measurementName))
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
    
    if (filename):
        figure.savefig(filename,dpi=200)
        
    return figure, axes

@ODMPlot(singleCycle=False,maxNumberOfCycles=_np.infty)
@_BasicProgressReporter(entryMessage="Creating multiple cycle voltage-displacement animation...")
def animateMultiCycleVoltageDisplacement(df, corrected=False, showReferenceValues=False, filename=None, measurementName="", nmPerPx=1, figure=None, axes=None, dpi=200, progressReporter=None):
    
    
    numberOfCycles = int(df.cycleNumber.max())    

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
    anim.save(filename, fps=10, extra_args=['-vcodec', 'libx264'],dpi=dpi)
    
    
    return anim

@ODMPlot(singleCycle=False)
@_BasicProgressReporter(entryMessage="Creating multiple cycle average graph...")
def plotMultiCycleMeanVoltageDisplacement(df,corrected=False,showReferenceValues=False, filename=None,measurementName="", nmPerPx=1, figure=None, axes=None):
    if not figure:
        figure = _plt.figure('Multiple cycle average %s (%s)' % ("(corrected)" if corrected else "", measurementName))
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
    
    if (filename):
        figure.savefig(filename,dpi=200)
        
    return figure,axes

@ODMPlot(multipleCycle=False,constantVoltage=True)
@_BasicProgressReporter(entryMessage="Creating intensity profile plots...")
def plotIntensityProfiles(dfRaw,movingPeakFitSettings,referencePeakFitSettings,numberOfProfiles=10,filename=None,measurementName="", nmPerPx=1, figure=None, axes=None):
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
    
    if (filename):
        figure.savefig(filename,dpi=200)
    
    return figure,axes
    
@ODMPlot(singleCycle=False,multipleCycle=False,constantVoltage=True)
@_BasicProgressReporter(entryMessage="Creating histogram for constant displacement...")
def plotConstantDisplacementHistogram(df,source='diff', nbins=None, filename=None, measurementName="", nmPerPx=1, figure=None, axes=None):
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

    
    if (filename):
        figure.savefig(filename,dpi=200)
        
    return figure,axes

@ODMPlot(constantVoltage=True)
@_BasicProgressReporter(entryMessage="Creating timestamp-displacement plot...")
def plotDisplacementVersusTimestamp(df,sources='diff',filename=None, measurementName="", nmPerPx=1, figure=None, axes=None):        
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
            #linearDriftValues = [m.linearDrift_diff for m in self.oda.measurementRecords]
        elif (source=='mp'):
            displacementValues = df.displacement_mp
            #linearDriftValues = [m.linearDrift_mp for m in self.oda.measurementRecords]
        elif (source=='ref'):
            displacementValues = df.displacement_ref
            #linearDriftValues = [m.linearDrift_ref for m in self.oda.measurementRecords]
                
        axes.plot(times,displacementValues,alpha=alpha,label=titlesDict[source])
        #axes.plot(times,linearDriftValues,'r--')
        
    axes.set_xlabel('Time (s)')
    axes.set_ylabel('Position (px)')
    
    if (len(sources)>1):
        axes.legend()
    
    tx = axes.twinx()
    tx.set_ylabel('Position (nm)')
    tx.set_ylim(nmPerPx * px for px in axes.get_ylim())
    
    if (filename):
        figure.savefig(filename,dpi=200)
    
