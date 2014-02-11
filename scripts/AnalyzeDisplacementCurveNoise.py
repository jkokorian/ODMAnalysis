# -*- coding: utf-8 -*-
"""
Created on Mon Oct 07 15:40:25 2013

@author: jkokorian
"""

import numpy as np
import scipy as cp
import odmanalysis.gui as gui
import odmanalysis as odm
import matplotlib.pyplot as plt
import sys
import os

##main script##

if (len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1])):
    filename = sys.argv[1]
else:
    filename = gui.get_path("*.csv",defaultFile="odmanalysis.csv")

commonPath = os.path.abspath(os.path.split(filename)[0])

try:
    settings = odm.CurveFitSettings.loadFromFile(commonPath + '/odmSettings.ini')
    print "settings loaded from local odmSettings.ini"
except:
    settings = gui.getSettingsFromUser(None)
    settings.saveToFile(commonPath + '/odmSettings.ini')
    print "settings saved to local odmSettings.ini"

nmPerPx = settings.pxToNm

df = odm.readAnalysisData(filename)
plt.plot(np.arange(len(df.displacement)),df.displacement*nmPerPx)

plt.interactive(False)
coordinateGrabber = gui.InteractiveCoordinateGrabber(plt.gcf(),2,"Select range for fitting a polynomial...")
coordinateGrabber.promptMessages = ["Select lower limit...","Select upper limit..."]
coordinates = coordinateGrabber.getValuesFromUser()

xLimits = [c[0] for c in coordinates]

dfs = df.iloc[slice(*xLimits)]


validInput = False
while (validInput == False):
    try:
        deg = int(raw_input("Polynomial degree: "))
        validInput = True
    except:
        pass
    
xValues = np.arange(len(dfs.displacement))
p = cp.polyfit(xValues,dfs.displacement,deg)
noise = (dfs.displacement - cp.polyval(p,xValues))*nmPerPx

ax = plt.subplot(111)
ax.plot(xValues,dfs.displacement*nmPerPx)
ax.plot(xValues,cp.polyval(p,xValues)*nmPerPx,'r--')
ax.set_xlabel("Actuator Voltage (V)")
ax.set_ylabel("Displacement (nm)")

fig, (ax1,ax2) = plt.subplots(nrows=1,ncols=2,sharex=False,sharey=True,squeeze=True)
ax1.plot(np.arange(len(noise)),noise,'o')
ax2.hist(noise,bins=50,orientation='horizontal',facecolor='green', alpha=0.5)
ax1.set_ylabel("Displacement (nm)")
ax2.set_xlabel("Count")
fig.savefig(os.path.join(commonPath,'Displacement noise.png'),dpi=150)

stats = noise.describe()
with open(os.path.join(commonPath,'position_noise_stats.txt'),'w') as f:
    f.write(str(stats));


plt.show()







