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
"""

import os
import sys
import odmanalysis as odm
from MakeODMPlots import makeDisplacementPlots, makeIntensityProfilePlots
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
    
    outputFilename = commonPath + "/odmanalysis.csv"
    
    readerProcess, readerQueue = startReadAsync(filename)
    dataProcessor = ChunkedODMDataProcessor(commonPath)
    chunkWriter = ChunkWriter(outputFilename)
    
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
    
    readerProcess.join()
    
    #make plots
    df = odm.readAnalysisData(outputFilename)
    settings = odm.CurveFitSettings.loadFromFile(commonPath + '/odmSettings.ini')
    makeDisplacementPlots(df,commonPath,measurementName,settings.pxToNm)

if __name__ == "__main__":
    main()
    
    