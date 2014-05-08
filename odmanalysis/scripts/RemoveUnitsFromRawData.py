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

Created on Thu Dec 19 15:14:41 2013

This script removes all units from the raw data.csv files that are written by
LabVIEW.

@author: jkokorian
"""

import odmanalysis.gui as gui
import os
import sys

def main():
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
        
if __name__ == "__main__":
    main()    