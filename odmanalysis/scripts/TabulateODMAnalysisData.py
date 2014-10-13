import pandas as pd
import odmanalysis as odm
from odmanalysis import gui
import os
import argparse




def main():

    parser = argparse.ArgumentParser(description='Pivots the odmanalysis output file to produce and excel file with all cycles in different columns')
    parser.add_argument('filename',
                        nargs='?',
                        default="",
                        help="The odmanalysis.csv file to tabulate",
                        type=str)
    parser.add_argument('--split-direction','-d',
                        type=bool,
                        help='split the actuation directions into different columns',
                        metavar='')
    args = parser.parse_args()
    if not os.path.isfile(args.filename):
        args.filename = gui.get_path("*.csv",defaultFile="odmanalysis.csv")
    
    commonPath = os.path.abspath(os.path.split(args.filename)[0])
    
    df = odm.readAnalysisData(args.filename)    
    
    cycleFrames = []
    keys = ['cycleNumber']
    if args.split_direction == True:
        keys.append('direction')
    grouped = df.groupby(keys)
    for keys, group in grouped:
        if not hasattr(keys, '__iter__'):
            keys = tuple([keys])
        dfTemp = group[['actuatorVoltage','displacement']]
        dfTemp = dfTemp.reset_index().drop('timestamp',axis=1)
        
        name = 'cycle_%i' % keys[0]
        for k in keys[1:]:
            name += "_%s" % k
        
        cycleFrames.append(pd.concat({name: dfTemp}, axis=1))
        
    dfCombined = pd.concat(cycleFrames,axis=1)
    dfCombined.to_excel(os.path.join(commonPath,'odmanalysis_tabulated.xlsx'),index=False)
    print os.path.join(commonPath,'odmanalysis_tabulated.xlsx')
    
if __name__=="__main__":
    main()
    