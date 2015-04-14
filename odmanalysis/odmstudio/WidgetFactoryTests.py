import unittest
from odmstudio_gui import WidgetFactory
from PyQt4.Qt import QLabel

class Test_WidgetFactoryTests(unittest.TestCase):
    def test_RegisterWidget(self):
        WidgetFactory.registerWidget(QLabel,str)

    def rest_RetreiveWidget(self):
        WidgetFactory.registerWidget(QLabel,str)
        self.assertTrue(WidgetFactory.getWidgetFor(str) == QLabel)

if __name__ == '__main__':
    unittest.main()
