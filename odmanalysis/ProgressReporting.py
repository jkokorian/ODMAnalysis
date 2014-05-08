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

Created on Thu Dec 19 10:29:54 2013

@author: jkokorian
"""


import sys

class ProgressReporter(object):
    """
    Abstract class definition for a ProgressReporter object.
    """
    def __init__(self):
        pass
    
    def progress(self,progress, message=""):
        pass
    
    def message(self,message):
        pass
        
    def done(self):
        pass
        

class StreamReporter(object):
    """
    A ProgressReporter that reports to a stream object.
    """
    def __init__(self,stream):
        """
        Parameters
        ----------
        
        stream: any stream-like object
            The stream to which progress is reported. The target stream object
            should at least have 'write' and 'flush' methods.
        """
        super(StreamReporter,self).__init__()
        self.stream = stream
        self.lastMessage = ""

    def progress(self,progress, message=""):
        s = "%s %d%%\r" % (message,progress)
        if (s != self.lastMessage):
            self.stream.write(s)
            self.stream.flush()
        self.lastMessage = s
    
    def message(self,message):
        if self.lastMessage.endswith("\n") or not self.lastMessage:
            s = "%s\r\n" % message
        else:
            s= "\r\n%s\r\n" % message
        self.stream.write(s)
        self.stream.flush()
        self.lastMessage = s
    
    def done(self):
        self.stream.write("\r\nDONE\r\n")
        self.stream.flush()

class StdOutProgressReporter(StreamReporter):
    """
    A ProgressReporter that reports to the standard output stream.
    """
    def __init__(self):
        StreamReporter.__init__(self,sys.stdout)
    

class BasicProgressReporter(object):
    """
    Decorator to provide basic progress reporting functionality to functions.
    
    Description
    -----------
    
    Functions that are decorated with this class will report a text message upon
    entry and exit. 
    
    If the decorated function has an arg or kwarg called 'progressReporter'
    that is not None, this Progressreporter will be used for reporting the entry and
    exiting of the function. 
    
    If the ProgressReporter argument is None, a StdOutputProgressReporter will be created
    upon decoration and passed to the function when it is called.

    
    Example
    -----

    Decorate any function as follows to use the standard entry and exit messages:
    
    >>> @BasicProgressReporter()
    ... def f():
    ...    pass
    >>> f()
    Executing f...
    Done
        
    Use the optional arguments to specify the enty and exit messages:
      
    >>> @BasicProgressReporter(entryMessage="entering...",exitMessage="exited")
    ... def f():
    ...    pass
    >>> f()
    entering...
    exited
    """
    
    def __init__(self, entryMessage = None, exitMessage = "Done"):
        """
        Parameters
        ----------
        
        entryMessage: string
            The message that will be displayed when the decorated function is called
        
        exitMessage: string
            The message that will be displayed when the decorated function exits
        """
        self.entryMessage = entryMessage
        self.exitMessage = exitMessage
        self.p = StdOutProgressReporter()
        
    def __call__(self,f):
        if self.entryMessage is None:
            self.entryMessage = "Executing %s..." % f.func_name
        
        def wrapped_f(*args,**kwargs):
            if (kwargs.has_key('progressReporter') and kwargs['progressReporter'] is not None):
                p = kwargs['progressReporter']
            else:
                
                p = self.p
                if 'progressReporter' in f.func_code.co_varnames:
                    kwargs['progressReporter'] = p
            
            p.message(self.entryMessage)
            result = f(*args,**kwargs)
                        
            p.message(self.exitMessage)
            return result
        
        wrapped_f.func_name = f.func_name
        return wrapped_f