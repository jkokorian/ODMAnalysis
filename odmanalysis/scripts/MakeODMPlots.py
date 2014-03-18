# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 11:29:47 2013

@author: jkokorian
"""

import sys as _sys
import os as _os
import odmanalysis as _odm
import odmanalysis.plots as odmp
import odmanalysis.gui as _gui
from matplotlib import pyplot as _plt

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
    
    kwargs = {'measurementName': measurementName, 'nmPerPx' : nmPerPx}
    odmPlots = odmp.ODMPlot.getSuitablePlotFunctions(df)
    for odmPlot in odmPlots:    
        odmPlot.runAndSave(df,savePath,**kwargs)
        
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

    if (len(_sys.argv) > 1 and _os.path.exists(_sys.argv[1]) and _os.path.isfile(_sys.argv[1])):
        filename = _sys.argv[1]
    else:
        filename = _gui.get_path("*.csv",defaultFile="odmanalysis.csv")
    
    
    commonPath = _os.path.abspath(_os.path.split(filename)[0])
    measurementName = _os.path.split(_os.path.split(filename)[0])[1]
    
    try:
        settings = _odm.CurveFitSettings.loadFromFile(commonPath + '/odmSettings.ini')
        print "settings loaded from local odmSettings.ini"
    except:
        settings = _gui.getSettingsFromUser(None)
        settings.saveToFile(commonPath + '/odmSettings.ini')
        print "settings saved to local odmSettings.ini"
    
    df = _odm.readAnalysisData(filename)
    
    makeDisplacementPlots(df,commonPath, measurementName = measurementName, nmPerPx = settings.pxToNm)
    
    
    _plt.show()

if __name__ == "__main__":
    main()
