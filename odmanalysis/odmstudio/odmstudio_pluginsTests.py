import unittest
import odmstudio_framework as framework


class Test_odmstudio_pluginsTests(unittest.TestCase):
    def test_plugins_module(self):
        plugins = framework.getPlugins()
        self.assertTrue(len(plugins) > 0)
        print plugins

if __name__ == '__main__':
    unittest.main()
