# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 11:29:47 2013

@author: jkokorian
"""

import sys
import os

import odmanalysis as odm
import odmanalysis.plots as odmp
import odmanalysis.gui as gui

from matplotlib import pyplot as plt

def makeDisplacementPlots(df,savePath,measurementName="",nmPerPx=1):
    """
    Creates all plots for the target odm analysis dataframe. Plots are saved to
    the savePath directory.
    
    The plot types that are created depends on the exact nature of the measurement 
    and are determined from the number of cycles, the actuator voltage and other stuff.
    
    The following plots are created for the different measurement types:
    
    fixed acutator voltage
    ----------------------    
    
    - A histogram of the measured displacements of:
        - the moving peak
        - the reference peak
        - the difference between those
    - The differential displacement versus time
    - The moving peak and reference peak displacements versus time
    
    
    single actuator voltage cycle
    -----------------------------
    
    - Voltage-displacement curve
    - The chi-square values of the moving peak and the reference peak resulting from the curve fit
    
    
    multiple actuator voltage cycles
    --------------------------------
    
    - Voltage-displacement curve for all cycles
    - Voltage-displacement curve for the displacement averaged over all cycles
    
    
    Parameters
    ----------
    
    df: pandas.DataFrame
        ODM dataframe that should contain at least the columns from the odmanalysis.csv file.
    savePath: string
        The path where the plot images should be saved to
    """
    
    showReferenceValues = odmp.hasReference(df)
    kwargs = {'measurementName': measurementName, 'nmPerPx' : nmPerPx}
            
    if odmp.hasConstantVoltage(df):
        print "Making plots for constant voltage"
        if showReferenceValues:
            odmp.plotConstantDisplacementHistogram(df,source='mp', filename = savePath + '/Position_histogram_mp.png', **kwargs)
            odmp.plotConstantDisplacementHistogram(df,source='ref', filename = savePath + '/Position_histogram_ref.png', **kwargs)
            odmp.plotConstantDisplacementHistogram(df,source='diff', filename = savePath + '/Position_histogram_diff.png', **kwargs)
            odmp.plotDisplacementVersusTimestamp(df,sources='diff', filename = savePath + '/Position-Timestamp_diff.png', **kwargs)
            odmp.plotDisplacementVersusTimestamp(df,sources='ref,mp', filename = savePath + '/Position-Timestamp_ref,mp.png', **kwargs)
        else:
            odmp.plotConstantDisplacementHistogram(df,source='mp',filename = savePath + '/Position_histogram.png', **kwargs)
            odmp.plotDisplacementVersusTimestamp(df,source='mp',filename = savePath + '/Position-Timestamp.png', **kwargs)
        
    else:
        odmp.plotChiSquare(df, filename = savePath +"/chi-squared.png", **kwargs)
        
        if odmp.hasMultipleCycles(df):
            if (df.cycleNumber.max() <= 200):
                odmp.plotMultiCycleVoltageDisplacement(df,corrected=False, showReferenceValues = showReferenceValues, filename = savePath +"/Voltage-Displacement.png", **kwargs)
                odmp.plotMultiCycleMeanVoltageDisplacement(df,corrected=False,showReferenceValues = showReferenceValues,filename = savePath +"/Voltage-Displacement_Mean.png", **kwargs)
            
            odmp.animateMultiCycleVoltageDisplacement(df,corrected=False, showReferenceValues = showReferenceValues, filename = savePath +"/Voltage-Displacement.mp4", **kwargs)
            
        else:
            odmp.plotSingleCycleVoltageDisplacement(df,corrected=False, showReferenceValues = showReferenceValues, filename = savePath +"/Voltage-Displacement.png", **kwargs)
            
            
    print "ALL DONE"
    
def makeIntensityProfilePlots(df,movingPeakFitSettings,referencePeakFitSettings,savePath, measurementName = "", nmPerPx = 1):
    """
    Creates plots of the intensity profiles with the fitted curves on top.
    
    Parameters
    ----------
    
    df : pandas.DataFrame
         ODM DataFrame that should contain at least the 'intensityProfile' column.
    movingPeakFitSettings : ODMAnalysisSimple.ODAFitSettings instance
        The fit settings for the moving peak.
    referencePeakFitSettings : ODMAnalysisSimple.ODAFitSettings instance
        The fit settings for the reference peak.
    savePath : string
        Path to the directory where the plots will be saved.
    measurementName : string
        Name of the measurement, will appear in the plot window titlebar.
    nmPerPx : float
        Number of nanometers per pixel, will appear on the second axis.
    """
    
    kwargs = {'measurementName': measurementName, 'nmPerPx' : nmPerPx}
    if 'intensityProfile' in df.columns:
        odmp.plotIntensityProfiles(df,movingPeakFitSettings,referencePeakFitSettings,numberOfProfiles=10, filename = savePath +"/IntensityProfiles.png",**kwargs)
    

def main():

    if (len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1])):
        filename = sys.argv[1]
    else:
        filename = gui.get_path("*.csv",defaultFile="odmanalysis.csv")
    
    
    commonPath = os.path.abspath(os.path.split(filename)[0])
    measurementName = os.path.split(os.path.split(filename)[0])[1]
    
    try:
        settings = odm.CurveFitSettings.loadFromFile(commonPath + '/odmSettings.ini')
        print "settings loaded from local odmSettings.ini"
    except:
        settings = gui.getSettingsFromUser(None)
        settings.saveToFile(commonPath + '/odmSettings.ini')
        print "settings saved to local odmSettings.ini"
    
    df = odm.readAnalysisData(filename)
    
    makeDisplacementPlots(df,commonPath, measurementName = measurementName, nmPerPx = settings.pxToNm)
    
    
    plt.show()

if __name__ == "__main__":
    main()
