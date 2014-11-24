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


class InteractiveStepViewer(qt.QWidget):
    def __init__(self,df,parent=None):
        qt.QWidget.__init__(self,parent)
        
        self.setWindowTitle("Interactive Intensity Profile Viewer")
        
        layout = qt.QVBoxLayout()        
        self.setLayout(layout)
        
        hLayout = qt.QHBoxLayout()
        layout.addLayout(hLayout)
        
        self.stepSlider = qt.QSlider(q.Qt.Horizontal)
        self.stepSlider.setTickPosition(qt.QSlider.TicksBothSides)
        self.stepSlider.setTickInterval(1)
        hLayout.addWidget(self.stepSlider)
        
        self.stepNumberLabel = qt.QLabel("step 1")
        hLayout.addWidget(self.stepNumberLabel)
                
        self.graph = pg.PlotWidget()
        layout.addWidget(self.graph)
        
        self.graph.setLabel('left', 'Intensity', units='a.u.')
        self.graph.setLabel('bottom', 'x', units='px')
        
        self.intensityProfilePlot = self.graph.plot(name="intensity profile")
        self.intensityProfilePlot.setPen((200,200,100))
         
        self.df = df
        self.stepSlider.setMinimum(1)
        self.stepSlider.setMaximum(len(df))

        

        # connect signals
        self.stepSlider.valueChanged.connect(self.showStep)
        self.stepSlider.valueChanged.connect(lambda i: self.stepNumberLabel.setText("step %i" % i))
        
        self.showStep(1)
        
    
    def showStep(self,stepNumber):
        df = self.df
        ip = df.intensityProfile.iloc[stepNumber]
        ip = ip-ip.mean()
        
        self.intensityProfilePlot.setData(x=_np.arange(len(ip)),y=ip)
        
    
def main():    
    if (len(_sys.argv) > 1 and _os.path.exists(_sys.argv[1]) and _os.path.isfile(_sys.argv[1])):
        filename = _sys.argv[1]
    else:
        filename = _gui.get_path("*.csv",defaultFile="data.csv")
    
    
    commonPath = _os.path.abspath(_os.path.split(filename)[0])
    measurementName = _os.path.split(_os.path.split(filename)[0])[1]
    
        
    df = _odm.readODMData(filename)
    
    app = qt.QApplication(_sys.argv)
    stepViewer = InteractiveStepViewer(df)
    stepViewer.show()
    app.exec_()

if __name__ == "__main__":
    main()
