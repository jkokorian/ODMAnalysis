
import PyQt4.QtCore as q
import PyQt4.QtGui as qt

class Observable(q.QObject):
    def __init__(self):
        q.QObject.__init__(self)

        self.bindings = {}

    def bind(self,instance,getter,setter,valueChangedSignal):
        binding = {"instance": instance,
                   "getter": getter,
                   "setter": setter,
                   "valueChangedSignal": valueChangedSignal}
        self.bindings[id(instance)] = binding
        self.initializeBinding(**binding)

    def initializeBinding(self,instance,getter,setter,valueChangedSignal):
        valueChangedSignal.connect(self.updateSubscribers)

    def updateSubscribers(self,value):
        if not isinstance(self.sender(),qt.QWidget) or (isinstance(self.sender(),qt.QWidget) and self.sender().hasFocus()):
            for instanceId, binding in self.bindings.iteritems():
                if instanceId != id(self.sender()) and (not isinstance(binding['instance'],qt.QWidget) or (isinstance(binding['instance'],qt.QWidget) and not binding['instance'].hasFocus())):
                    binding['setter'](value)
                    print "value updated on %s" % instanceId


class Model(q.QObject):
    
    valueChanged = q.pyqtSignal(int)
    
    def __init__(self):
        q.QObject.__init__(self)
        self.value = 0

    def setValue(self, value):
        if (self.value != value):
            self.value = value
            self.valueChanged.emit(value)

    def getValue(self):
        return value



class TestWidget(qt.QWidget):
    def __init__(self):
        qt.QWidget.__init__(self,parent=None)
        layout = qt.QVBoxLayout()

        spinbox1 = qt.QSpinBox()
        spinbox2 = qt.QSpinBox()
        button = qt.QPushButton()

        self.model = Model()

        valueObserver = Observable()
        self.valueObserver = valueObserver
        valueObserver.bind(spinbox1,spinbox1.value,spinbox1.setValue,spinbox1.valueChanged)
        valueObserver.bind(spinbox2,spinbox2.value,spinbox2.setValue,spinbox2.valueChanged)
        valueObserver.bind(self.model,self.model.getValue,self.model.setValue,self.model.valueChanged)

        button.clicked.connect(lambda: self.model.setValue(10))

        layout.addWidget(spinbox1)
        layout.addWidget(spinbox2)
        layout.addWidget(button)

        self.setLayout(layout)

#QtGui.QApplication.setGraphicsSystem('raster')


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    app = qt.QApplication([])

    w = TestWidget()
    w.show()

    
    
    
    
    import sys
    if (sys.flags.interactive != 1) or not hasattr(q, 'PYQT_VERSION'):
        qt.QApplication.instance().exec_()
