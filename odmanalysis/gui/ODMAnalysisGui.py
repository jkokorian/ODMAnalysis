# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 13:46:39 2013

@author: jkokorian
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import wx
import sys
from .. import FitFunctions
import matplotlib.pyplot as plt
from matplotlib import patches
from .. import ODMAnalysis as ODM


def get_path(wildcard,defaultFile=""):
    app = wx.App(None)
    style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    dialog = wx.FileDialog(None, 'Open', wildcard=wildcard, style=style,defaultFile=defaultFile)
    if dialog.ShowModal() == wx.ID_OK:
        path = dialog.GetPath()
    else:
        path = None
    dialog.Destroy()
    app.MainLoop()
    app.Exit()
    app.Destroy()
    return path

class Cursor:
    def __init__(self, ax):
        self.ax = ax
        self.lx = ax.axhline(color='k')  # the horiz line
        self.ly = ax.axvline(color='k')  # the vert line

        # text location in axes coords
        self.txt = ax.text( 0.7, 0.9, '', transform=ax.transAxes)
        
        ax.figure.canvas.mpl_connect('motion_notify_event', self.mouse_move)

    def mouse_move(self, event):
        if not event.inaxes: return

        x, y = event.xdata, event.ydata
        # update the line positions
        self.lx.set_ydata(y )
        self.ly.set_xdata(x )

        self.txt.set_text( 'x=%1.2f, y=%1.2f'%(x,y) )
        self.ax.figure.canvas.draw()


class SnaptoCursor:
    """
    Like Cursor but the crosshair snaps to the nearest x,y point
    For simplicity, I'm assuming x is sorted
    """
    def __init__(self, ax, x, y):
        self.ax = ax
        self.lx = ax.axhline(color='k')  # the horiz line
        self.ly = ax.axvline(color='k')  # the vert line
        self.x = x
        self.y = y
        # text location in axes coords
        self.txt = ax.text( 0.7, 0.9, '', transform=ax.transAxes)
        
    def mouse_move(self, event):

        if not event.inaxes: return

        x, y = event.xdata, event.ydata

        indx = searchsorted(self.x, [x])[0]
        x = self.x[indx]
        y = self.y[indx]
        # update the line positions
        self.lx.set_ydata(y )
        self.ly.set_xdata(x )

        self.txt.set_text( 'x=%1.2f, y=%1.2f'%(x,y) )
        print ('x=%1.2f, y=%1.2f'%(x,y))
        self.ax.figure.canvas.draw()


class ClickDisplayer:
    def __init__(self,axes):
        self.figure = axes.figure
        self.axes = axes
        self.cid = None
        self.enable()
    
    def __onCanvasClick(self, event):
        if (event.inaxes == self.axes):
            circle = patches.Circle((event.xdata,event.ydata),radius=0.5)
            self.axes.add_artist(circle)
            self.figure.canvas.draw()
            
    
    def enable(self):
        if (self.cid == None):
            self.cid = self.axes.figure.canvas.mpl_connect('button_press_event', self.__onCanvasClick)
    
    def disable(self):
        if (self.cid != None):
            self.axes.figure.canvas.mpl_disconnect(self.cid)
            self.cid = None

class InteractiveCoordinateGrabber(object):
    def __init__(self,figure,numberOfValues=1,title=""):
        self.figure = figure
        self.axes = figure.gca()
        self.cursor = Cursor(self.axes)
        self.clickDisplayer = ClickDisplayer(self.axes)
        self.values = []
        self.numberOfValues = numberOfValues
        self.cid = None
        self.enable()
        self.grabCompleted = []
        self.promptMessages = ["" for i in range(numberOfValues)]
        self.figure.canvas.set_window_title(title)
        
    def __onCanvasClick(self,event):
        if (event.inaxes == self.axes):
            self.values.append((event.xdata,event.ydata))
            if (len(self.values) == self.numberOfValues):
                self.disable()
            
            self.axes.set_title(self.promptMessages.pop(0))
                
                
    def enable(self):
        self.clickDisplayer.enable()        
        if (self.cid == None):
            self.cid = self.figure.canvas.mpl_connect('button_press_event',self.__onCanvasClick)
        
    def disable(self):
        self.clickDisplayer.disable()
        if (self.cid != None):
            self.figure.canvas.mpl_disconnect(self.cid)
    
    def getValuesFromUser(self):        
        self.promptMessages.append("close graph to continue")
        self.axes.set_title(self.promptMessages.pop(0))
        plt.show()
        return self.values


class CurveFitSettingsDialog(QDialog):
    def __init__(self,fitFunctions,curveFitSettings):
        super(CurveFitSettingsDialog,self).__init__()
        self.fitFunction = None
        self.fitFunctions = fitFunctions[:]
                
        self.fitFunctionLabel = QLabel("Fit Function")
        self.fitFunctionComboBox = QComboBox()
        self.fitFunctionComboBox.addItems([f.getName() for f in fitFunctions])
        if (curveFitSettings.defaultFitFunction is not ""):
            defaultIndex = [ff.getName() for ff in self.fitFunctions].index(curveFitSettings.defaultFitFunction)
            self.fitFunctionComboBox.setCurrentIndex(defaultIndex)
        
        self.fitFunctionLabel.setBuddy(self.fitFunctionComboBox)
        
        self.nmPerPx = curveFitSettings.pxToNm
        self.resolutionLabel = QLabel("Resolution")
        self.resolutionSpinBox = QDoubleSpinBox()
        self.resolutionSpinBox.setMinimum(0.1)
        self.resolutionSpinBox.setMaximum(10000000)
        self.resolutionSpinBox.setSuffix(" nm/px")
        self.resolutionLabel.setBuddy(self.resolutionSpinBox)
        self.resolutionSpinBox.setValue(self.nmPerPx)
        
        self.xkcd = curveFitSettings.xkcd
        self.xkcdLabel = QLabel("xkcd style graphs")
        self.xkcdCheckBox = QCheckBox()
        self.xkcdCheckBox.setChecked(self.xkcd)
            
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        
        grid = QGridLayout()
        grid.addWidget(self.fitFunctionLabel,0,0)
        grid.addWidget(self.fitFunctionComboBox,0,1)
        grid.addWidget(self.resolutionLabel,1,0)
        grid.addWidget(self.resolutionSpinBox,1,1)
        grid.addWidget(self.xkcdLabel,2,0)
        grid.addWidget(self.xkcdCheckBox,2,1)
        grid.addWidget(buttonBox,3,0,1,2)    
        self.setLayout(grid)
        
        self.connect(buttonBox, SIGNAL("accepted()"),self, SLOT("accept()"))
        self.connect(buttonBox, SIGNAL("rejected()"),self, SLOT("reject()"))
        self.setWindowTitle("Choose fit function")

    def accept(self):
        self.fitFunction = self.fitFunctions[self.fitFunctionComboBox.currentIndex()]
        self.nmPerPx = self.resolutionSpinBox.value()
        self.xkcd = self.xkcdCheckBox.isChecked()
        QDialog.accept(self)
    
    def getFitFunction(self):
        return self.fitFunction
    
    def getNmPerPx(self):
        return self.nmPerPx
    
    def getXkcd(self):
        return self.xkcd
        
        
class StandaloneCurveFitSettingsDialog(QApplication):
    def __init__(self,argv,fitFunctions,curveFitSettings):
        super(StandaloneCurveFitSettingsDialog,self).__init__(argv)
        self.dialog = CurveFitSettingsDialog(fitFunctions,curveFitSettings)
        self._hasClosed = False
        self.connect(self, SIGNAL("lastWindowClosed()"),self.onClose)
        
    def exec_(self):
        self.dialog.show()
        super(StandaloneCurveFitSettingsDialog,self).exec_()
        
    def getFitFunction(self):
        return self.dialog.getFitFunction()
        
    def getNmPerPx(self):
        return self.dialog.getNmPerPx()
    
    def onClose(self): 
        self._hasClosed = True
    
    def getXkcd(self):
        return self.dialog.getXkcd()


def getSettingsFromUser(curveFitSettings):
    """
    Show the Curve Fit settings dialog and saves the results to the target settings object.
    Returns the selected fit-function and the resolution in nm per pixel
    """
    if not curveFitSettings:
        curveFitSettings = ODM.CurveFitSettings()
    
    fitFunctions = FitFunctions.createFitFunctions()
    app = StandaloneCurveFitSettingsDialog(sys.argv,fitFunctions,curveFitSettings)
    app.exec_()
    
    curveFitSettings.pxToNm = app.getNmPerPx()
    curveFitSettings.defaultFitFunction = app.getFitFunction().getName()
    curveFitSettings.xkcd = app.getXkcd()
    
    return curveFitSettings


def getPeakFitSettingsFromUser(intensityProfile,fitFunction,windowTitle="Estimates",estimatorPromptPrefix=""):
    fig = plt.figure()
    plt.plot(intensityProfile)
    
    estimatorDefinitions = fitFunction.getEstimatorDefinitions()
    
    
    if (any([ed.id == "minBound" for ed in estimatorDefinitions]) == False):
        estimatorDefinitions.append(FitFunctions.EstimatorDefinition('minBound',"Select Lower x Limit"))
    if (any([ed.id == "maxBound" for ed in estimatorDefinitions]) == False):
        estimatorDefinitions.append(FitFunctions.EstimatorDefinition('maxBound',"Select Upper x Limit"))
    
    for ed in estimatorDefinitions:
        ed.promptMessage = "%s\n%s" % (estimatorPromptPrefix,ed.promptMessage)
    
    cg = InteractiveCoordinateGrabber(fig,len(estimatorDefinitions),windowTitle)
    cg.promptMessages = [ed.promptMessage for ed in estimatorDefinitions]
    values = cg.getValuesFromUser()
    estimatorValuesDict = dict((estimatorDefinitions[i].id,values[i]) for i in range(len(estimatorDefinitions)))
    
    fitSettings = ODM.ODAFitSettings(fitFunction,estimatorValuesDict)
    fitSettings.fitFunction = fitFunction
    
    return fitSettings


    
    