
import PyQt4.QtCore as q
import PyQt4.QtGui as qt

class Binding(object):
    def __init__(self,instance,getter,setter,valueChangedSignal):
        self.instanceId = id(instance)
        self.instance = instance
        self.getter = getter
        self.setter = setter
        self.valueChangedSignal = valueChangedSignal

        

class Observer(q.QObject):
    def __init__(self):
        q.QObject.__init__(self)

        self.bindings = {}
        self.ignoreEvents = False

    def bind(self,instance,getter,setter,valueChangedSignal):
        binding = Binding(instance,getter,setter,valueChangedSignal)
        self.bindings[binding.instanceId] = binding
        valueChangedSignal.connect(self.updateSubscribers)


    def updateSubscribers(self,*args,**kwargs):
        sender = self.sender()
        if not self.ignoreEvents:
            self.ignoreEvents = True

            for binding in self.bindings.values():
                if binding.instanceId == id(sender):
                    continue

                binding.setter(*args,**kwargs)

            self.ignoreEvents = False
        
                        

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

        valueObserver = Observer()
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
