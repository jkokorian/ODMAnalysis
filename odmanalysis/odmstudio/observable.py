
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

    def bindProperty(self,instance,propertyName):
        getterAttribute = getattr(instance,propertyName)
        if callable(getterAttribute):
            #the propertyName turns out to be a method (like value()), assume the corresponding setter is called setValue()
            getter = getterAttribute
            if len(propertyName) >  1:
                setter = getattr(instance,"set" + propertyName[0].upper() + propertyName[1:])
            else:
                setter = getattr(instance,"set" + propertyName[0].upper())
        else:
            getter = lambda: getterAttribute()
            setter = lambda value: setattr(instance,propertyName,value)

        valueChangedSignal = getattr(instance,propertyName + "Changed")

        self.bind(instance,getter,setter,valueChangedSignal)

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
        self.__value = 0

    @property
    def value(self):
        return self.__value
    
    @value.setter
    def value(self, value):
        if (self.__value != value):
            self.__value = value
            self.valueChanged.emit(value)




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
        valueObserver.bindProperty(spinbox1, "value")
        valueObserver.bindProperty(spinbox2, "value")
        valueObserver.bindProperty(self.model, "value")

        button.clicked.connect(lambda: setattr(self.model,"value",10))

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
