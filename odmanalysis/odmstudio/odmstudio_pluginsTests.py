import unittest

class Test_odmstudio_pluginsTests(unittest.TestCase):
    def test_plugins_module(self):
        from plugins.someplugin import kenker as k
        k.knakermethod()
        

if __name__ == '__main__':
    unittest.main()
