import pandas as pd
import odmanalysis as odm
from odmanalysis import gui
import os
import sys



def main():
    if (len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1])):
        filename = sys.argv[1]
    else:
        filename = gui.get_path("*.csv",defaultFile="odmanalysis.csv")
    
    commonPath = os.path.abspath(os.path.split(filename)[0])
    
    
    df = odm.readAnalysisData(filename)    
    
    cycleFrames = []
    grouped = df.groupby(['cycleNumber','direction'])
    for (cycleNumber,direction), group in grouped:
        dfTemp = group[['actuatorVoltage','displacement']]
        dfTemp = dfTemp.reset_index().drop('timestamp',axis=1)
        
        name = 'cycle_%i_%s' % (cycleNumber,direction)
        
        cycleFrames.append(pd.concat({name: dfTemp}, axis=1))
    
    dfCombined = pd.concat(cycleFrames,axis=1)
    dfCombined.to_excel(os.path.join(commonPath,'odmanalysis_tabulated.xlsx'))
    print os.path.join(commonPath,'odmanalysis_tabulated.xlsx')
    
if __name__=="__main__":
    main()
    