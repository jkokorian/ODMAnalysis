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
import odmanalysis.gui as gui
from FitRawODMData import fitRawODMData
from MakeODMPlots import makeDisplacementPlots, makeIntensityProfilePlots

import os
import matplotlib.pyplot as plt
import argparse



def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile",type=str,nargs="?",default=None)
    parser.add_argument("--settings-file",dest="odm_settings_file",type=str,default=None,
    		help="an odmSettings.ini file to get the settings from")
    parser.add_argument("--fitfunction-params-file",dest="fitfunction_params_file",type=str,default=None,
    		help="a json file with the fitfunction parameters to use")
    parser.add_argument("--show",dest="show_plots",action="store_true")
    parser.add_argument("--noshow",dest="show_plots",action="store_false")
    parser.add_argument("--separate-cycles",dest="separate_cycles",action="store_true")
    parser.add_argument("--remove-incomplete-cycles",dest='remove_incomplete_cycles',action="store_true")
    parser.set_defaults(show_plots=True,separate_cycles=False,remove_incomplete_cycles=False)
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
    
    
    commonPath = os.path.abspath(os.path.split(datafile)[0])
    measurementName = os.path.split(commonPath)[1]
    
    df,settings,movingPeakFitSettings,referencePeakFitSettings,measurementName = fitRawODMData(datafile,
                                                                                               settingsFile=odmSettingsFile,
                                                                                               fitSettingsFile=ffSettingsFile,
                                                                                               fitCyclesSeparately=args.separate_cycles,
                                                                                               removeIncompleteCycles=args.remove_incomplete_cycles)
    
    
    plotKwargs = {'savePath' : commonPath, 'measurementName' : measurementName, 'nmPerPx' : settings.pxToNm}
    print "creating plots..."
    makeDisplacementPlots(df, **plotKwargs)
    makeIntensityProfilePlots(df, movingPeakFitSettings,referencePeakFitSettings, **plotKwargs)
    
    print "ALL DONE"
    if args.show_plots == True:
        plt.show()


if __name__=="__main__":
    main()    