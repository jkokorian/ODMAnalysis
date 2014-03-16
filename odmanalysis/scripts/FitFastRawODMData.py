
import os
import sys
import odmanalysis as odm
from odmanalysis import gui
from odmanalysis.chunkhandling import ChunkedODMDataProcessor,ChunkWriter
from multiprocessing import Process, Queue


def readAsync(outputQueue,inputFile):
    reader = odm.getODMDataReader(inputFile)
    for chunk in reader:
        outputQueue.put(chunk)

def startReadAsync(inputFile):
    q = Queue(1)
    p = Process(target=readAsync, args=(q,inputFile))
    p.start()
    return p,q

def main():
    if (len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1])):
        filename = sys.argv[1]
    else:
        filename = gui.get_path("*.csv",defaultFile="data.csv")    

    commonPath = os.path.abspath(os.path.split(filename)[0])
    
    measurementName = os.path.split(os.path.split(filename)[0])[1]
    
    
    readerProcess, readerQueue = startReadAsync(filename)
    dataProcessor = ChunkedODMDataProcessor(filename)
    chunkWriter = ChunkWriter(commonPath + "/odmanalysis.csv")
    
    while True:
        try:        
            rawChunk = readerQueue.get(timeout=10)
        except:
            #done
            break            
        
        rawChunk = rawChunk[rawChunk.intensityProfile.map(len) > 0]
        if len(rawChunk) is not 0:
            processedChunk = dataProcessor.processDataFrame(rawChunk)
            chunkWriter.writeDataFrame(processedChunk)
        
            
if __name__ == "__main__":
    main()
    
    