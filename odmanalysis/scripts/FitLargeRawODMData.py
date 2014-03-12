
import os
import sys
import odmanalysis as odm
from odmanalysis import gui
from ODMWatchdog import AsyncRawODMDataFitter

def main():
    if (len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1])):
        filename = sys.argv[1]
    else:
        filename = gui.get_path("*.csv",defaultFile="data.csv")
    
    commonPath = os.path.abspath(os.path.split(filename)[0])
    outputFile = os.path.join(commonPath, "odmanalysis.csv")
    
    rawDataProcessor = AsyncRawODMDataFitter(filename,outputFile)
    rawDataProcessor.startPCChain()

if __name__ == "__main__":
    main()