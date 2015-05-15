import unittest
from odmstudio_framework import WidgetFactory,RegisterWidgetFor
from PyQt4.Qt import QLabel,QWidget

class Test_WidgetFactoryTests(unittest.TestCase):
    def test_RegisterWidget(self):
        WidgetFactory.registerWidget(QLabel,str)

    def test_RetreiveWidget(self):
        WidgetFactory.registerWidget(QLabel,str)
        self.assertTrue(WidgetFactory.getWidgetClassFor(str) == QLabel)

    def test_RegisterWidgetForDecorator(self):
        @RegisterWidgetFor(float)
        class Test(QWidget):
            pass

        self.assertTrue(WidgetFactory.getWidgetClassFor(float) == Test)



if __name__ == '__main__':
    unittest.main()
