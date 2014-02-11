# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 15:14:41 2013

This script removes all units from the raw data.csv files that are written by
LabVIEW.

@author: jkokorian
"""

import odmanalysis.gui as gui
import os
import sys

if __name__ == "__main__":
    if (len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1])):
        filename = sys.argv[1]
    else:
        filename = gui.get_path("*.csv",defaultFile="data.csv")
    
    commonPath = os.path.abspath(os.path.split(filename)[0])   
    
    
    with file(filename,'r') as fIn:
        with file(filename+'new','w') as fOut:
            for line in fIn:
                fOut.write(line.replace(" s","").replace(" V",""))
    
    os.rename(filename,filename+".old")
    os.rename(filename+"new",filename)
    os.remove(filename+".old")
    print "DONE"
        