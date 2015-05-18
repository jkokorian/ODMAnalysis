from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import odmstudio_gui as gui
import odmanalysis.odmstudio.odmstudio_framework as fw

fw.loadPlugins()

#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
#mw = QtGui.QMainWindow()
#mw.resize(800,800)

w = gui.ODMStudioMainWindow()
w.show()


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
