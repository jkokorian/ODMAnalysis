# -*- coding: utf-8 -*-
"""
Created on Sat Aug 17 16:00:14 2013

@author: jkokorian
"""

import os
import sys
import odmanalysis as odm
import odmanalysis.gui as gui
import odmanalysis.fitfunctions as ff
import pickle

def fitRawODMData(filename):
    """
    Script that opens analyzes the target data.csv file produced by LabVIEW and
    analyzes the optical displacement of a peak relative to another peak.
    
    Parameters
    ----------
    
    filename: string
        Path to the data.csv file produced by LabVIEW that contains the raw 
        Optical Displacement Measurement Data.
    
    
    Returns
    -------
    
    dataframe: pandas.DataFrame
        A dataframe that contains the raw data, the calculated displacements,
        curve fit results and other diagnostic data.
    movingPeakFitSettings : CurveFitSettings instance
        The curve fit settings used for the moving peak.
    referencePeakFitSettings: CurveFitSettings instance
        The curve fit settings used for the reference peak.
    measurementName: string
        The name of the measurement (deduced from the folder name of the csv file)
    """
    
    commonPath = os.path.abspath(os.path.split(filename)[0])
    measurementName = os.path.split(os.path.split(filename)[0])[1]
    
    globalSettings = odm.CurveFitSettings.loadFromFileOrCreateDefault('./CurveFitScriptSettings.ini')
    
    settings = odm.CurveFitSettings.loadFromFileOrCreateDefault(commonPath + '/odmSettings.ini',prototype=globalSettings)
    
    df = odm.readODMData(filename)
    
    gui.getSettingsFromUser(settings)
    
    movingPeakFitFunction = ff.createFitFunction(settings.defaultFitFunction)
    movingPeakFitSettings = gui.getPeakFitSettingsFromUser(df.intensityProfile[1],movingPeakFitFunction,
                                                       estimatorPromptPrefix="Moving peak:",
                                                       windowTitle="Moving Peak estimates")
    
    try:
        referencePeakFitFunction = ff.createFitFunction(settings.defaultFitFunction)
        referencePeakFitSettings = gui.getPeakFitSettingsFromUser(df.intensityProfile[1],referencePeakFitFunction,
                                                                  estimatorPromptPrefix="Reference peak:",
                                                                  windowTitle="Reference Peak estimates")
    except: #exception occurs if user cancels the 'dialog'
        referencePeakFitFunction = None        
        referencePeakFitSettings = None
        print 'no reference'
    
    print "fitting a %s function..." % settings.defaultFitFunction
    df_movingPeak = odm.calculatePeakDisplacements(df.intensityProfile, movingPeakFitSettings, factor=100,maxfev=20000)
    
    df_movingPeak.rename(columns = lambda columnName: columnName + "_mp",inplace=True)
    df = df.join(df_movingPeak)
    
    if (referencePeakFitSettings is not None):
        df_referencePeak = odm.calculatePeakDisplacements(df.intensityProfile, referencePeakFitSettings, factor=100,maxfev=20000)
        df_referencePeak.rename(columns = lambda columnName: columnName + "_ref",inplace=True)
        df = df.join(df_referencePeak)
        df['displacement'] = df.displacement_mp - df.displacement_ref
    else:
        df['displacement'] = df.displacement_mp
    
    
    #save settings
    sys.stdout.write("saving defaults...")
    globalSettings.saveToFile()
    sys.stdout.write("done\r\n")
    
    sys.stdout.write("saving local setting file...")
    settings.saveToFile()
    sys.stdout.write("done\r\n")
    
    print "done"    
    
    sys.stdout.write("saving dataframe as csv file...")
    exportColumns = ['relativeTime','cycleNumber','direction','actuatorVoltage','displacement','displacement_mp','chiSquare_mp']
    if ('displacement_ref' in df.columns):
        exportColumns +=['displacement_ref','chiSquare_ref']
    df[exportColumns].to_csv(os.path.join(commonPath,'odmanalysis.csv'),index_label='timestamp')
    sys.stdout.write("done\r\n")
    
    sys.stdout.write("pickling fit results dataframe as pcl file...")
    fitResultColumns = ['curveFitResult_mp']
    if 'curveFitResult_ref' in df.columns:
        fitResultColumns += ['curveFitResult_ref']
    df[fitResultColumns].save(commonPath + '/fitResults.pcl')
    sys.stdout.write("done\r\n")
    
    sys.stdout.write("pickling fit functions and settings...")
    settingsDict = {'movingPeakFitSettings': movingPeakFitSettings,
                             'referencePeakFitSettings': referencePeakFitSettings if referencePeakFitSettings is not None else None}
    with file(commonPath+'/fitSettings.pcl','w') as stream:
        pickle.dump(settingsDict,stream)
    sys.stdout.write("done\r\n")
    
    print "ALL DONE"
    
    return df,movingPeakFitSettings,referencePeakFitSettings,measurementName


##main script##
if __name__ == "__main__":
    if (len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1])):
        filename = sys.argv[1]
    else:
        filename = gui.get_path("*.csv",defaultFile="data.csv")
    

    df,movingPeakFitSettings,referencePeakFitSettings,measurementName = fitRawODMData(filename)
    
    raw_input("press any key to close")
    
    
    

    
    