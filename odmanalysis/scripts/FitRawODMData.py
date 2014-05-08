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

def fitRawODMData(filename):
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
    
    globalSettings = odm.CurveFitSettings.loadFromFileOrCreateDefault('./CurveFitScriptSettings.ini')
    
    settings = odm.CurveFitSettings.loadFromFileOrCreateDefault(commonPath + '/odmSettings.ini',prototype=globalSettings)
    
    df = odm.readODMData(filename)
    
    gui.getSettingsFromUser(settings)
    
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
    
    return df,movingPeakFitSettings,referencePeakFitSettings,measurementName

##main script##
def main():

    if (len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1])):
        filename = sys.argv[1]
    else:
        filename = gui.get_path("*.csv",defaultFile="data.csv")
    

    df,movingPeakFitSettings,referencePeakFitSettings,measurementName = fitRawODMData(filename)
    
    raw_input("press any key to close")
    
    
    
if __name__ == "__main__":
    main()
    
    