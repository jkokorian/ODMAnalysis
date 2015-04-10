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

Created on Fri Dec 20 11:29:47 2013

@author: jkokorian
"""

import sys as _sys
import os as _os
import odmanalysis as _odm
import odmanalysis.gui as _gui
from PyQt4 import QtCore as q
from PyQt4 import QtGui as qt
import pyqtgraph as pg
import numpy as _np


class InteractiveCycleViewer(qt.QWidget):
    def __init__(self,df,parent=None):
        qt.QWidget.__init__(self,parent)
        
        self.setWindowTitle("Interactive Voltage-Displacement Cycle Viewer")
        
        layout = qt.QVBoxLayout()        
        self.setLayout(layout)
        
        hLayout = qt.QHBoxLayout()
        layout.addLayout(hLayout)
        
        self.cycleSlider = qt.QSlider(q.Qt.Horizontal)
        self.cycleSlider.setTickPosition(qt.QSlider.TicksBothSides)
        self.cycleSlider.setTickInterval(1)
        hLayout.addWidget(self.cycleSlider)
        
        self.cycleNumberLabel = qt.QLabel("cycle 1")
        hLayout.addWidget(self.cycleNumberLabel)
                
        self.graph = pg.PlotWidget()
        layout.addWidget(self.graph)
        
        self.graph.setLabel('left', 'Displacement', units='nm')
        self.graph.setLabel('bottom', 'Voltage', units='V')
        
        self.forwardPlot = self.graph.plot(name="forward")
        self.forwardPlot.setPen((200,200,100))
        self.backwardPlot = self.graph.plot(name="backward")
        self.backwardPlot.setPen((100,200,200))
        
        self.graph.addLegend()
        
        self.df = df
        self.cycleSlider.setMinimum(1)
        self.cycleSlider.setMaximum(int(df.cycleNumber.max()))

        

        # connect signals
        self.cycleSlider.valueChanged.connect(self.showCycle)
        self.cycleSlider.valueChanged.connect(lambda i: self.cycleNumberLabel.setText("cycle %i" % i))
        
        self.showCycle(1)
        
    
    def showCycle(self,cycleNumber):
        df = self.df
        dfFwd = df[(df.cycleNumber == cycleNumber) & (df.direction == 'forward')]
        dfBwd = df[(df.cycleNumber == cycleNumber) & (df.direction == 'backward')]
        self.forwardPlot.setData(x=_np.array(dfFwd.actuatorVoltage),y=_np.array(dfFwd.displacement_nm))
        self.backwardPlot.setData(x=_np.array(dfBwd.actuatorVoltage),y=_np.array(dfBwd.displacement_nm))
        
    
def main():    
    if (len(_sys.argv) > 1 and _os.path.exists(_sys.argv[1]) and _os.path.isfile(_sys.argv[1])):
        filename = _sys.argv[1]
    else:
        filename = _gui.get_path("*.csv",defaultFile="odmanalysis.csv")
    
    
    commonPath = _os.path.abspath(_os.path.split(filename)[0])
    measurementName = _os.path.split(_os.path.split(filename)[0])[1]
    
    
    print "loading settings from " + commonPath + "/odmSettings.ini"
    settings = _odm.CurveFitSettings.loadFromFile(commonPath+"/odmSettings.ini")
    df = _odm.readAnalysisData(filename)
    df['displacement_nm'] = df.displacement * settings.pxToNm      
    
    
    app = qt.QApplication(_sys.argv)
    cycleViewer = InteractiveCycleViewer(df)
    cycleViewer.show()
    app.exec_()

if __name__ == "__main__":
    main()
