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
    
    def progress(self,progress, message=""):
        s = "%s %d%%\r" % (message,progress)
        if (s != self.lastMessage):
            sys.stdout.write(s)
            sys.stdout.flush()
        self.lastMessage = s
    
    def message(self,message):
        if self.lastMessage.endswith("\n") or not self.lastMessage:
            s = "%s\r\n" % message
        else:
            s= "\r\n%s\r\n" % message
        sys.stdout.write(s)
        sys.stdout.flush()
        self.lastMessage = s
    
    def done(self):
        sys.stdout.write("\r\nDONE\r\n")
        sys.stdout.flush()


class BasicProgressReporter(object):
    """
    Decorator to provide basic progress reporting functionality to functions.
    """
    def __init__(self, entryMessage = None, exitMessage = None):
        self.entryMessage = entryMessage
        self.exitMessage = exitMessage
        self.p = StdOutProgressReporter()
            
    def __call__(self,f):
        if self.entryMessage is None:
            self.entryMessage = "executing %s..." % f.func_name
        if self.exitMessage is None:
            self.exitMessage = "done"
        
        def wrapped_f(*args,**kwargs):
            if (kwargs.has_key('progressReporter') and kwargs['progressReporter'] is not None):
                p = kwargs['progressReporter']
            else:
                
                p = self.p
                if 'progressReporter' in f.func_code.co_varnames:
                    kwargs['progressReporter'] = p
            
            p.message(self.entryMessage)
            f(*args,**kwargs)
            p.message(self.exitMessage)
        
        wrapped_f.func_name = "%s_BasicProgressReporter" % f.func_name
        return wrapped_f