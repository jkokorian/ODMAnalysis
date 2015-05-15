import unittest
import odmstudio_lib as lib

class Test_SourceReaderFactory(unittest.TestCase):
    

    def test_getSourceReaderRegistrations(self):
        registrations = lib.SourceReaderFactory.getSourceReaderRegistrations()
        self.assertTrue(len(registrations) > 0)

        for r in registrations:
            self.assertTrue(all([issubclass(r.sourceReaderType,lib.SourceReader) for r in registrations]))

if __name__ == '__main__':
    unittest.main()
