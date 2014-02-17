# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 11:11:00 2013

@author: jkokorian

This script opens and analyzes the target data.csv file produced by LabVIEW and
analyzes the optical displacement of a peak relative to another peak.

Results are saved to the same folder as the original data file. Depending on the
measurement type (which is determined from the data found in 'data.csv', a number
of graphs is produced and saved.)

This script calls the 'FitRawODMData' script (which only produces raw output data)
under the hood.
"""

import odmanalysis as odm
import odmanalysis.gui as gui
from FitRawODMData import fitRawODMData
from MakeODMPlots import makeDisplacementPlots, makeIntensityProfilePlots

import os
import sys
import matplotlib.pyplot as plt



##main script##
def main():
    if (len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1])):
        filename = sys.argv[1]
    else:
        filename = gui.get_path("*.csv",defaultFile="data.csv")
    
    commonPath = os.path.abspath(os.path.split(filename)[0])
    measurementName = os.path.split(os.path.split(filename)[0])[1]
    
    settings = odm.CurveFitSettings.loadFromFileOrCreateDefault(commonPath + '/odmSettings.ini')
    print "settings loaded from local odmSettings.ini"
    
    df,movingPeakFitSettings,referencePeakFitSettings,measurementName = fitRawODMData(filename)
    
    plotKwargs = {'savePath' : commonPath, 'measurementName' : measurementName, 'nmPerPx' : settings.pxToNm}
    print "creating plots..."
    makeDisplacementPlots(df, **plotKwargs)
    makeIntensityProfilePlots(df, movingPeakFitSettings,referencePeakFitSettings, **plotKwargs)
    
    print "ALL DONE"
    plt.show()


if __name__=="__main__":
    main()    