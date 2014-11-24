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

Created on Sat Aug 17 16:00:14 2013

@author: jkokorian
"""

import os
import sys
import odmanalysis as odm
import odmanalysis.gui as gui
import odmanalysis.fitfunctions as ff
import pickle
import argparse
import pandas as _pd
import subprocess


def fitRawODMData(filename,settingsFile=None,fitSettingsFile=None,fitCyclesSeparately=False,removeIncompleteCycles=False):
    """
    This script opens and analyzes the target data.csv file produced by LabVIEW and
    analyzes the optical displacement of a peak relative to another peak.
    Results are saved to the same folder as the original data file.
    
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
    
    globalSettings = odm.CurveFitSettings.loadFromFileOrCreateDefault(os.path.expanduser('~') + '/odmSettings.ini')
    
    if (settingsFile is not None):
        print "reading settings from %s" % settingsFile
        templateSettings = odm.CurveFitSettings.loadFromFile(settingsFile)
        settings = odm.CurveFitSettings.loadFromFileOrCreateDefault(commonPath + '/odmSettings.ini',prototype=templateSettings)
    else:
        settings = odm.CurveFitSettings.loadFromFileOrCreateDefault(commonPath + '/odmSettings.ini',prototype=globalSettings)
        gui.getSettingsFromUser(settings)

    
    df = odm.readODMData(filename)
    odm.removeIncompleteCycles(df)
    
    if (fitSettingsFile is not None):
        with file(fitSettingsFile,'r') as f:
            print "reading fit settings from %s" % fitSettingsFile
            settingsDict = pickle.load(f)
            movingPeakFitSettings = settingsDict['movingPeakFitSettings']
            referencePeakFitSettings = settingsDict['referencePeakFitSettings']
        
    else:
        movingPeakFitFunction = ff.createFitFunction(settings.defaultFitFunction)
        movingPeakFitSettings = gui.getPeakFitSettingsFromUser(df.intensityProfile.iloc[1],movingPeakFitFunction,
                                                           estimatorPromptPrefix="Moving peak:",
                                                           windowTitle="Moving Peak estimates")
        
        try:
            referencePeakFitFunction = ff.createFitFunction(settings.defaultFitFunction)
            referencePeakFitSettings = gui.getPeakFitSettingsFromUser(df.intensityProfile.iloc[1],referencePeakFitFunction,
                                                                      estimatorPromptPrefix="Reference peak:",
                                                                      windowTitle="Reference Peak estimates")
        except: #exception occurs if user cancels the 'dialog'
            referencePeakFitFunction = None        
            referencePeakFitSettings = None
            print 'no reference'
        
    print "fitting a %s function..." % settings.defaultFitFunction
    print "fitting moving peak..."
    if (fitCyclesSeparately):
        movingPeakDataFrames = []        
        for cycleNumber,group in df.groupby('cycleNumber'):
            print "Cycle %i" % cycleNumber
            df_movingPeak = odm.calculatePeakDisplacements(group.intensityProfile, movingPeakFitSettings, factor=100,maxfev=20000)
            movingPeakDataFrames.append(df_movingPeak)
        df_movingPeak = _pd.concat(movingPeakDataFrames)
    
    else:    
        df_movingPeak = odm.calculatePeakDisplacements(df.intensityProfile, movingPeakFitSettings, factor=100,maxfev=20000)
    
    df_movingPeak.rename(columns = lambda columnName: columnName + "_mp",inplace=True)
    df = df.join(df_movingPeak)
    
    if (referencePeakFitSettings is not None):
        print "fitting reference peak..."
        if (fitCyclesSeparately):
            referencePeakDataFrames = []
            for cycleNumber,group in df.groupby('cycleNumber'):
                print "Cycle %i" % cycleNumber
                df_referencePeak = odm.calculatePeakDisplacements(group.intensityProfile, referencePeakFitSettings, updateInitialParameters=False, factor=100,maxfev=20000)
                referencePeakDataFrames.append(df_referencePeak)
            df_referencePeak = _pd.concat(referencePeakDataFrames)
        else:
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
    
    #save calculated peak position data as csv
    sys.stdout.write("saving dataframe as csv file...")
    exportColumns = ['relativeTime','cycleNumber','direction','actuatorVoltage','displacement','displacement_mp','chiSquare_mp']
    if ('displacement_ref' in df.columns):
        exportColumns +=['displacement_ref','chiSquare_ref']
    df[exportColumns].to_csv(os.path.join(commonPath,'odmanalysis.csv'),index_label='timestamp')
    sys.stdout.write("done\r\n")
    
    #save fit results as pickled dataframe
    sys.stdout.write("pickling fit results dataframe as pcl file...")
    fitResultColumns = ['curveFitResult_mp']
    if 'curveFitResult_ref' in df.columns:
        fitResultColumns += ['curveFitResult_ref']
    df[fitResultColumns].to_pickle(commonPath + '/fitResults.pcl')
    sys.stdout.write("done\r\n")
    
    #save the used fit functions and fit settings as pickled objects
    sys.stdout.write("pickling fit functions and settings...")
    settingsDict = {'movingPeakFitSettings': movingPeakFitSettings,
                             'referencePeakFitSettings': referencePeakFitSettings if referencePeakFitSettings is not None else None}
    with file(commonPath+'/fitSettings.pcl','w') as stream:
        pickle.dump(settingsDict,stream)
    sys.stdout.write("done\r\n")
    
    print "ALL DONE"
    
    return df,settings,movingPeakFitSettings,referencePeakFitSettings,measurementName

##main script##
def main():
    
    
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile",type=str,nargs="?",default=None)
    parser.add_argument("--settings-file",dest="odm_settings_file",type=str,default=None,
    		help="an odmSettings.ini file to get the settings from")
    parser.add_argument("--fitfunction-params-file",dest="fitfunction_params_file",type=str,default=None,
    		help="a json file with the fitfunction parameters to use")
    
    args = parser.parse_args()

    if (not args.datafile is None and os.path.exists(args.datafile) and os.path.isfile(args.datafile)):
        datafile = args.datafile
    else:
        datafile = gui.get_path("*.csv",defaultFile="data.csv")
        
    if (not args.odm_settings_file is None and os.path.exists(args.odm_settings_file) and os.path.isfile(args.odm_settings_file)):
        odmSettingsFile = args.odm_settings_file
    else:
        odmSettingsFile = None
    
    if (not args.fitfunction_params_file is None and os.path.exists(args.fitfunction_params_file) and os.path.isfile(args.fitfunction_params_file)):
        ffSettingsFile = args.fitfunction_params_file
    else:
        ffSettingsFile = None

    df,settings,movingPeakFitSettings,referencePeakFitSettings,measurementName = fitRawODMData(datafile,settingsFile=odmSettingsFile,fitSettingsFile=ffSettingsFile)
    
    
if __name__ == "__main__":
    main()
    
    