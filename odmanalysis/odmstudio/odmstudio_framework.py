import PyQt4.QtGui as qt
import PyQt4.QtCore as q

class WidgetFactory(object):
    
    __dict = {}
    
    @classmethod
    def registerWidget(cls,widgetClass,anyClass):
        cls.__dict[anyClass] = widgetClass

    @classmethod
    def getWidgetClassFor(cls,anyClass):
        if cls.__dict.has_key(anyClass):
            return cls.__dict[anyClass]
        else:
            return None

class RegisterWidgetFor(object):
    def __init__(self,targetClass):
        """
        Decorate a QWidget class to register it as the preferred GUI component for a (non widget) class.
        """
        assert not issubclass(targetClass,qt.QWidget)
        self.targetClass = targetClass

    def __call__(self,qWidgetClass):
        assert issubclass(qWidgetClass,qt.QWidget)
        
        WidgetFactory.registerWidget(qWidgetClass,self.targetClass)

        return qWidgetClass


class SourceReaderRegistration(object):
    def __init__(self,sourceReaderType,fileType,extensions,maxNumberOfFiles):
        self.sourceReaderType = sourceReaderType
        self.fileType = fileType
        self.extensions = extensions
        self.maxNumberOfFiles = maxNumberOfFiles

    def getFilterString(self):
        extensionString = " ".join(["*.%s" % ext for ext in self.extensions])
        return "%s (%s)" % (self.fileType,extensionString)

    def __str__(self):
        return "%s: %s" % (self.getFilterString(),self.sourceReaderType)


class SourceReaderFactory(object):
    _sourceReaderRegistrations = []

    @classmethod
    def registerSourceReader(cls,sourceReaderRegistration):
        cls._sourceReaderRegistrations.append(sourceReaderRegistration)

    @classmethod
    def getSourceReaderForExtension(cls, extension): 
        sourceReaders = [sr for sr in cls._sourceReaderRegistrations if extension in sr.extensions]
        if len(sourceReaders) >= 1:
            return sourceReaders[0]
        else:
            return None
    
    @classmethod
    def hasSourceReaderForExtension(cls,extension):
        return cls.getSourceReaderForExtension(extension) is not None

    @classmethod
    def getSourceReaderRegistrations(cls):
        return [srr for srr in cls._sourceReaderRegistrations]

class RegisterSourceReader(object):
    """
    Decorate classes that inherit from SourceReader with this method to indicate what kind of files the sourcereader handles and register it with the SourceReaderFactory
    """

    

    def __init__(self, fileType, extensions=(), maxNumberOfFiles=1):
        self.fileType = fileType
        self.extensions = extensions
        self.maxNumberOfFiles = maxNumberOfFiles;

    def __call__(self,cls):
        srRegistration = SourceReaderRegistration(cls,self.fileType,self.extensions,self.maxNumberOfFiles)
        SourceReaderFactory.registerSourceReader(srRegistration)
        
        return cls




class FeatureTrackerFactory(object):
    _featureTrackers = []

    @classmethod
    def registerFeatureTracker(cls,featureTracker):
        cls._featureTrackers.append(featureTracker)


    @classmethod
    def getFeatureTrackers(cls):
        return [ft for ft in cls._featureTrackers]


class RegisterFeatureTracker(object):
    """
    Decorate classes that inherit from FeatureTracker with this method to register them with the FeatureTrackerFactory.
    """


    def __init__(self, name=""):
        self.name = name

    def __call__(self,cls):
        
        FeatureTrackerFactory.registerFeatureTracker(cls)
        return cls

######################################################
#PLUGINS
######################################################

import imp
import os

pluginRoot = "./plugins"
_pluginModules = []

def getPlugins():
    pluginFolders = [f for f in [os.path.join(pluginRoot,f) for f in os.listdir(pluginRoot)] if os.path.isdir(f) and "__init__.py" in os.listdir(f)]

    plugins = []
    for pluginFolder in pluginFolders:
        plugins += [dict(name=f.rstrip(".py"),path=pluginFolder,info=imp.find_module(f.rstrip(".py"),[pluginFolder])) for f in os.listdir(pluginFolder) if f.endswith(".py") and f != "__init__.py"]

    return plugins

def loadPlugins():
    global _pluginModules
    _pluginModules = [imp.load_module(plugin['name'], *plugin["info"]) for plugin in getPlugins()]
        