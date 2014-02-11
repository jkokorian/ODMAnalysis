# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 09:57:12 2013

@author: jkokorian
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mpld
from .. import ODMStats


def hasMultipleCycles(odmAnalysisDataFrame):
    return len(odmAnalysisDataFrame.cycleNumber.unique()) > 1

def hasReference(odmAnalysisDataFrame):
    return 'displacement_ref' in odmAnalysisDataFrame.columns

def hasConstantVoltage(odmAnalysisDataFrame):
    return len(odmAnalysisDataFrame.actuatorVoltage.unique()) == 1

    
def plotChiSquare(df, filename=None, measurementName="", figure = None, axes = None, nmPerPx=1):
    if not figure:    
        figure = plt.figure('Chi-Squared (%s)' % measurementName)
    if not axes:
        axes = plt.subplot(111)
    
    axes.plot(df.actuatorVoltage,df.chiSquare_mp,label='moving peak')
    if (hasReference(df)):
        axes.plot(df.actuatorVoltage,df.chiSquare_ref,label='reference')
    
    axes.set_title('$\chi$-Squared')
    axes.set_ylabel("$\chi^2$")
    axes.set_xlabel("Actuator Voltage (V)")

    if (filename):
        figure.savefig(filename,dpi=200)
    
    return figure,axes



def plotSingleCycleVoltageDisplacement(df, corrected=False, showReferenceValues=False, filename=None, measurementName="", nmPerPx=1, figure = None, axes = None):
    #show voltage-displacement curve
    if not figure:    
        figure = plt.figure('Voltage Displacement %s (%s)' % ("(corrected)" if corrected else "", measurementName))
    if not axes:
        axes = plt.subplot(111)
    
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



def plotMultiCycleVoltageDisplacement(df, corrected=False, showReferenceValues=False, filename=None, measurementName="", nmPerPx=1, figure=None, axes=None):
    if not figure:    
        figure = plt.figure('Multiple cycles %s (%s)' % ("(corrected)" if corrected else "", measurementName))
    if not axes:
        axes = plt.subplot(111)
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

def plotMultiCycleMeanVoltageDisplacement(df,corrected=False,showReferenceValues=False, filename=None,measurementName="", nmPerPx=1, figure=None, axes=None):
    if not figure:
        figure = plt.figure('Multiple cycle average %s (%s)' % ("(corrected)" if corrected else "", measurementName))
    if not axes:
        axes = plt.subplot(111)
    axes.set_ylabel("Displacement (px)")
    axes.set_xlabel("Actuator Voltage (V)")
    
    grouped = df.groupby(['direction','actuatorVoltage'])['displacement']
    dfMean = grouped.agg({'displacement': np.mean})
    dfMean.displacement['forward'].plot(ax=axes,label="forward")
    dfMean.displacement['backward'].plot(ax=axes,label="backward")
    
    axes.legend()        
    
    tx = axes.twinx()
    tx.set_ylabel('Displacement (nm)')
    tx.set_ylim(nmPerPx * px for px in axes.get_ylim())
    
    if (filename):
        figure.savefig(filename,dpi=200)
        
    return figure,axes

def plotIntensityProfiles(dfRaw,movingPeakFitSettings,referencePeakFitSettings,numberOfProfiles=10,filename=None,measurementName="", nmPerPx=1, figure=None, axes=None):
    if not figure:
        figure = plt.figure('Intensity Profiles (%s)' % measurementName)
    if not axes:
        axes = plt.subplot(111)
    axes.set_xlabel('x (px)')
    axes.set_ylabel('Intensity (arb. units)')
    
    for i in range(0,len(dfRaw.intensityProfile),len(dfRaw.intensityProfile)//numberOfProfiles):
        
        xValues_mp = np.arange(movingPeakFitSettings.xminBound,movingPeakFitSettings.xmaxBound)
        
        plt.plot(dfRaw.intensityProfile[i],'b')
        plt.plot(xValues_mp,movingPeakFitSettings.fitFunction(xValues_mp,*dfRaw.curveFitResult_mp[i].popt),'r--')
        
        if referencePeakFitSettings:
            xValues_ref = np.arange(referencePeakFitSettings.xminBound,referencePeakFitSettings.xmaxBound)                
            plt.plot(xValues_ref,referencePeakFitSettings.fitFunction(xValues_ref,*dfRaw.curveFitResult_ref[i].popt),'g--')
    
    ty = axes.twiny()
    ty.set_xlabel('x ($\mu$m)')
    ty.set_xlim(nmPerPx / 1000 * px for px in axes.get_xlim())
    
    if (filename):
        figure.savefig(filename,dpi=200)
    
    return figure,axes
    

def plotConstantDisplacementHistogram(df,source='diff', nbins=None, filename=None, measurementName="", nmPerPx=1, figure=None, axes=None):
    titlesDict = {'diff': 'differential','mp': 'moving peak', 'ref': 'reference peak'}
    
    if not figure:    
        figure = plt.figure('Position histogram: %s (%s)' % (titlesDict[source], measurementName))
    if not axes:
        axes = plt.subplot(111)
    histogramKwargs = {'facecolor':'green', 'alpha':0.5,'normed': True}
    
    if (source == 'diff'):
        displacementValues = df.displacement
        
    elif (source == 'mp'):
        displacementValues = df.displacement_mp
        
    elif (source == 'ref'):
        displacementValues = df.displacement_ref
    
    if not nbins:
        nbins = int(round(np.sqrt(len(displacementValues))))
    
    plt.hist(displacementValues,bins=nbins,**histogramKwargs)
    
    sd = ODMStats.makeStatsDescriptionDict(displacementValues * nmPerPx)
    peakDistanceToEdge = [abs(sd['mean']-x*nmPerPx) for x in axes.get_xlim()]
    xtext = 0.1 if peakDistanceToEdge[0] > peakDistanceToEdge[1] else 0.7
        
    plt.text(xtext,0.7,ODMStats.printStatsDescriptionDict(sd),transform=axes.transAxes)
    plt.xlabel('position (px)')
    ty = axes.twiny()
    ty.set_xlabel('position (nm)')
    ty.set_xlim(nmPerPx * px for px in axes.get_xlim())

    
    if (filename):
        figure.savefig(filename,dpi=200)
        
    return figure,axes

def plotDisplacementVersusTimestamp(df,sources='diff',filename=None, measurementName="", nmPerPx=1, figure=None, axes=None):        
    sources = sources.split(',')
    
    titlesDict = {'diff': 'differential','mp': 'moving peak', 'ref': 'reference peak'}
    title = ', '.join(titlesDict[s] for s in sources)
    if not figure:    
        figure = plt.figure('Position-Time %s (%s)' % (title,measurementName))
    if not axes:
        axes = plt.subplot(111)
    
    
    times = mpld.date2num(df.index)
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
    
