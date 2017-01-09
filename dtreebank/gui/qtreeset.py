from PyQt4.QtCore import *
from PyQt4.QtGui import *

from dtreebank.core.treeset import TreeSet
from dtreebank.core.tree import Tree

import datetime


class TreeQTProxy(QObject):

    """Implements the slots of a tree"""
    
    def __init__(self,tree):
        QObject.__init__(self)
        self.tree=tree
        
class TreeQ(Tree):

    """Wraps all methods which should emit a signal"""

    maxEditInactivity=datetime.timedelta(seconds=10)

    def __init__(self):
        Tree.__init__(self)
        self.qtProxy=TreeQTProxy(self)
        self.lastEditTime=None #When was this tree edited for the very last time?
        self.lastEditSessionStart=None
        self.pausedTimer=None
        self.activelyEdited=False #Set to True if we are being actively edited
        self.editCount=0

    def hasChanged(self,context):
        Tree.hasChanged(self)
        self.qtProxy.emit(SIGNAL("treeChanged()"))
        self.treeset.searchDirty=True
        if context in (u"editor",):
            self.recordEditTime()
            self.editCount+=1

    def recordEditTime(self):
        if not self.activelyEdited:
            self.startEditing()
            return
        if self.userInactive(): #Whoops - user edits after a long delay
            if self.userAdmitsBeingInactive():
                self.stopEditing(self.lastEditTime)
            else:
                self.stopEditing(self.pausedTimer,force=True)
            self.pausedTimer=None
            self.startEditing()
        self.lastEditTime=datetime.datetime.now()
    
    def userAdmitsBeingInactive(self):
        self.pausedTimer=datetime.datetime.now()
        timeDiff=datetime.datetime.now()-self.lastEditTime
        msg="%02dm%02ds passed since your last edit at %s (now is %s). Have you been annotating in that time or not?"%(timeDiff.seconds//60,timeDiff.seconds%60,self.lastEditTime.strftime("%H:%M:%S"),datetime.datetime.now().strftime("%H:%M:%S"))
        answer=QMessageBox.question(None,"Inactivity correction",msg,"Not annotating","Annotating")
        return answer==0

    def stopEditing(self,atTime=None,force=False):
        #If atTime is None, current time will be used
        if self.activelyEdited==False:
            return #nothing to do
        if atTime==None and self.userInactive():
            if self.userAdmitsBeingInactive():
                atTime=self.lastEditTime
            else:
                force=True
                atTime=self.pausedTimer
            self.pausedTimer=None
            
        self.activelyEdited=False
        if atTime==None:
            atTime=datetime.datetime.now()
        assert self.lastEditSessionStart!=None 
        if force or self.editCount>0:
            self.eh.recordEditSession(beg=self.lastEditSessionStart,end=atTime)
        self.lastEditTime=None
        self.lastEditSessionStart=None
        self.editCount=0
        self.qtProxy.emit(SIGNAL("editingStopped()"))
        

    def startEditing(self,atTime=None):
        if self.activelyEdited==True:
            return #nothing to do
        if atTime==None:
            atTime=datetime.datetime.now()
        self.lastEditSessionStart=atTime
        self.lastEditTime=atTime
        self.activelyEdited=True
        self.qtProxy.emit(SIGNAL("editingStarted()"))
        
        
    def correctedStopTime(self,currentAtTime):
        if currentAtTime==None:
            currentAtTime=datetime.datetime.now()
        #Checks whether the currentAtTime is within acceptable limits from last edit
        timeDiff=datetime.datetime.now()-self.lastEditTime
        #Is there a suspicious break?
        if timeDiff>TreeQ.maxEditInactivity:
            #We have a problem; the user has been inactive for too long
            #maybe one wants to correct for this...
            if self.userAdmitsBeingInactive():
                self.pausedTimer=None
                return self.lastEditTime
            else:
                pausedTimer=self.pausedTimer
                self.pausedTimer=None
                return pausedTimer
        return currentAtTime

    def editTimeInfo(self):
        if self.lastEditSessionStart!=None:
            if self.pausedTimer!=None:
                reference=self.pausedTimer
            else:
                reference=datetime.datetime.now()
            timeDiff=reference-self.lastEditSessionStart+self.eh.totalEditTime
            return timeDiff
        else:
            return self.eh.totalEditTime
        

    def userInactive(self):
        return self.activelyEdited and datetime.datetime.now()-self.lastEditTime > TreeQ.maxEditInactivity




class TreeSetQTProxy(QObject):

    """Implements the slots of a treeset"""
    
    def __init__(self,treeset):
        QObject.__init__(self)
        self.treeset=treeset

    @pyqtSignature("")
    def treeChanged(self):
        self.treeset.treeChanged()
        self.emit(SIGNAL("treesetDirty(PyQt_PyObject)"),self.treeset.fileName)


class TreeSetQ(TreeSet):

    """Wraps all methods which should emit a signal"""

    treeClass=TreeQ #The class used to make new trees within

    @classmethod
    def fromFile(cls,fileName):
        return super(TreeSetQ,cls).fromFile(fileName)

    def __init__(self,*args,**kargs):
        TreeSet.__init__(self,*args,**kargs)
        self.qtProxy=TreeSetQTProxy(self)
        self.searchDirty=True #A flag marking whether this treeset should be reloaded before next search
        

    def appendTree(self,tree):
        TreeSet.appendTree(self,tree)
        QObject.connect(tree.qtProxy,SIGNAL("treeChanged()"),self.qtProxy,SLOT("treeChanged()"))


    def appendTreeAfter(self,currentTree,newTree): #Called by a sentence when split into two
        TreeSet.appendTreeAfter(self,currentTree,newTree)
        QObject.connect(newTree.qtProxy,SIGNAL("treeChanged()"),self.qtProxy,SLOT("treeChanged()"))

    def announceStatus(self):
        if self.dirty:
            self.qtProxy.emit(SIGNAL("treesetDirty(PyQt_PyObject)"),self.fileName)
        else:
            self.qtProxy.emit(SIGNAL("treesetClean(PyQt_PyObject)"),self.fileName)

    def save(self):
        TreeSet.save(self)
        self.qtProxy.emit(SIGNAL("treesetClean(PyQt_PyObject)"),self.fileName)

    def treeChanged(self):
        TreeSet.treeChanged(self)
            
            
        
