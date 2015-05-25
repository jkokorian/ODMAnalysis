from odmanalysis.odmstudio import odmstudio_lib as lib
from odmanalysis.odmstudio import odmstudio_framework as framework
import odmanalysis as odm
import pandas as pd

@framework.RegisterSourceReader("Comma separated", extensions=['csv'], maxNumberOfFiles=1)
class CsvReader(lib.SourceReader):
    

    def __init__(self, dataSource):
        lib.SourceReader.__init__(self, dataSource)
        

    def read(self):
        super(CsvReader,self).read()
        
        self._setStatusMessage("reading...")
        reader = odm.getODMDataReader(self.sourcePath,chunksize=500)
        
        lineCount = float(sum(1 for line in open(self.sourcePath)))
        chunks = []
        linesRead = 1
        for chunk in reader:
            linesRead += 500
            self.appendChunkToData(chunk)
            self._setStatusMessage("%i lines read" % linesRead)
            self._setProgress(linesRead/lineCount * 100)

        self._setStatusMessage("File loaded")
        self._setProgress(100)
        

    def appendChunkToData(self,chunk):
        if self.dataSource.sourceIsEmpty:
            self.dataSource.setSourceDataFrame(chunk)
        else:
            self.dataSource.setSourceDataFrame(pd.concat([self.dataSource.sourceDataFrame,chunk]))        