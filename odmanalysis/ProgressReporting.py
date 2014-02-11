# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 10:29:54 2013

@author: jkokorian
"""

import sys

class ProgressReporter(object):
    def __init__(self):
        pass
    
    def progress(self,progress):
        raise NotImplementedError("Should be implemented by children")
    
    def message(self,message):
        raise NotImplementedError("Should be implemented by children")
        
    def done(self):
        raise NotImplementedError("Should be implemented by children")
        

class StdOutProgressReporter(ProgressReporter):
    def __init__(self):
        super(StdOutProgressReporter,self).__init__()
        self.lastMessage = ""
    
    def progress(self,progress):
        s = "%d%%\r" % (progress)
        if (s != self.lastMessage):
            sys.stdout.write(s)
            sys.stdout.flush()
        self.lastMessage = s
    
    def message(self,message):
        sys.stdout.write("\r\n %s \r\n" % message)
    
    def done(self):
        sys.stdout.write("\r\nDONE\r\n")
        sys.stdout.flush()