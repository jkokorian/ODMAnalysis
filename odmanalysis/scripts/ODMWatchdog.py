"""
    Copyright (C) 2014 Delft University of Technology, The Netherlands

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Created on Sun Dec 15 13:50:25 2013

@author: jkokorian
"""

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys
import os
from Queue import Queue, Full
import odmanalysis.gui as gui
from odmanalysis.chunkhandling import ChunkedODMDataProcessor, ChunkReader, ChunkWriter, ReturnActionConsumerThread

class OMDCsvChunkHandler(FileSystemEventHandler):
    """
    Handler for watchdog filesystem events.
    
    Description
    -----------
    
    This class hosts three consumer/producer threads for the following functions
    
        - producer: reading chunks of data from the input file.
        - consumer-producer: processing chunks of data
        - consumer: writing chunks of data to the output file
        
    When a change is detected on the target input file a flag is raised to the
    'reader' thread to read a chunk of data. This chunk is then passed on to the
    dataProcessing consumer thread where the displacement is detected and stored to an
    output dataframe. This dataframe is passed to the outputwriter consumer thread that
    writes it to the output csv file.
    """    
    
    def __init__(self,inputFile,outputFile):
        self.inputFile = inputFile
        
        self.fileQueue = Queue(1)
        self.rawDataframeQueue = Queue()
        self.processedDataframeQueue = Queue()
        
        self.chunkReader = ChunkReader(inputFile)
        self.dataProcessor = ChunkedODMDataProcessor(os.path.abspath(os.path.split(inputFile)[0]))
        self.chunkWriter = ChunkWriter(outputFile)
        
        self.fileConsumerThread = ReturnActionConsumerThread(self.chunkReader.read_next,self.fileQueue,self.rawDataframeQueue)
        self.odmProcessorThread = ReturnActionConsumerThread(self.dataProcessor.processDataFrame,self.rawDataframeQueue,self.processedDataframeQueue)
        self.outputWriterThread = ReturnActionConsumerThread(self.chunkWriter.writeDataFrame,self.processedDataframeQueue)
        
        
        
    def on_modified(self, event):
        if (event.src_path == self.inputFile):
            try:
                self.fileQueue.put((),block=False)
            except Full:
                pass
    
    def startPCChain(self):
        self.fileConsumerThread.start()
        self.odmProcessorThread.start()
        self.outputWriterThread.start()
    
    def stopPCChain(self):
        pass
        

def main():
    if (len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1])):
        filename = sys.argv[1]
    else:
        filename = gui.get_path("*.csv",defaultFile="data.csv")
    
    commonPath = os.path.abspath(os.path.split(filename)[0])
    outputFile = os.path.join(commonPath, "odmanalysis.csv")
    
    print "Now watching %s for changes" % filename
    handler = OMDCsvChunkHandler(filename,outputFile)
    observer = Observer()
    observer.schedule(handler, path=commonPath, recursive=False)
    handler.startPCChain()
    observer.start()

    try:
        while True:
            time.sleep(1)
                
    except (KeyboardInterrupt, SystemExit):
        print "Stopping..."
        observer.stop()
        time.sleep(1)
    observer.join()
    

if __name__ == "__main__":
    main()