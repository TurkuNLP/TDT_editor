from dtreebank.gui.qtreeset import TreeSetQ, TreeQ
from dtreebank.gui.treeseteditor_ui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
import os
import os.path

import re

from dtreebank.core.treeset import *
from dtreebank.gui.treesearchform import *
from dtreebank.gui.helpform import *
from dtreebank.gui.aboutform import *
#from treesetmenu import Treeset

import traceback
import xml.etree.cElementTree as ET

try:
    import psyco
    psyco.full()
except:
    print >> sys.stderr, "Psyco not found"


fileNameRe=re.compile("^([a-z]+)([0-9]+)")

class FileNameAction(QAction):
    """Treesets menu action"""

    def __init__(self,fileName,parent):
        QAction.__init__(self,fileName,parent)
        self.fileName=fileName
        assert self.connect(self,SIGNAL("triggered()"),self,SLOT("emitTriggeredWithName()"))

    def getFileNameComponents(self):
        #For name like wn0001blahblah returns ("wn",0001)
        #otherwise returns None
        match=fileNameRe.match(os.path.basename(self.fileName))
        if not match:
            return None
        else:
            return match.group(1),int(match.group(2))

    @pyqtSignature("")
    def emitTriggeredWithName(self):
        self.emit(SIGNAL("selectedFileName(PyQt_PyObject)"),self.fileName)

    @pyqtSignature("PyQt_PyObject")
    def treesetDirty(self,fileName):
        assert self.fileName==fileName
        if not self.text().startsWith("*"):
            self.setText(u"*"+self.text())
    
    @pyqtSignature("PyQt_PyObject")
    def treesetClean(self,fileName):
        assert self.fileName==fileName
        if self.text().startsWith("*"):
            self.setText(self.text()[1:])
            

            

        

class TreeSetEditor(QMainWindow):
    # Filename filter for "open file" dialogs. Alternatives
    # are separated by two semicolons.
    openFileFilenameFilter = "Annotator XML files (*.xml);; Tab-delimited files (*.conll09 *.conllx *.conll *.txt)"

    def __init__(self,fileList=[],parent=None):
        QMainWindow.__init__(self,parent)
        self.gui=Ui_TreeSetEditor()
        self.gui.setupUi(self)
        self.completeGui()
        self.setupSignals()
        self.setWidgetDefaults()

        self.treeSets=[]
        self.currentTreesetIdx=None

        self.searchDirty=False #Has the data changed so that search re-init is necessary?

        if fileList:
            self.openFiles(fileList)


    def completeGui(self): #does stuff I couldn't do in QDesigner...
        self.gui.editTimeElapsedLabel=QLabel("--:--")
        self.gui.editTimeElapsedLabel.setToolTip("Time spent annotating this sentence (min:sec)")
        self.gui.editTimeElapsedLabel.setTextFormat(Qt.AutoText)
        self.gui.timeBar.addWidget(self.gui.editTimeElapsedLabel)
        self.gui.halfSecondTimer=QTimer(self)
        self.gui.halfSecondTimer.setInterval(500)
        self.gui.halfSecondTimer.start()

        self.gui.actionStopEditTiming.setDisabled(True)
        self.gui.actionStopAtLastEdit.setDisabled(True)

        spacer=QWidget()
        spacer.setFixedWidth(10)
        self.gui.timeBar.addWidget(spacer)
        self.gui.timeBar.addWidget(QLabel("Timeout:"))

        spacer=QWidget()
        spacer.setFixedWidth(10)
        self.gui.timeBar.addWidget(spacer)

        self.gui.timeoutWidget=QComboBox()
        self.gui.timeoutWidget.addItems(["0:10","0:30","1:00","1:30","2:00","3:00","4:00","5:00"])
        self.gui.timeoutWidget.setToolTip("Annotator inactivity timeout (min:sec)")
        self.gui.timeBar.addWidget(self.gui.timeoutWidget)

        spacer=QWidget()
        spacer.setFixedWidth(10)
        self.gui.toolBar.addWidget(spacer)
        self.gui.toolBar.addWidget(QLabel("Font size:"))
        spacer=QWidget()
        spacer.setFixedWidth(10)
        self.gui.toolBar.addWidget(spacer)
        self.gui.fontsizeWidget=QComboBox()
        self.gui.fontsizeWidget.addItems(["4", "6", "8", "10", "12", "14", "16"])
        # we set this before signals, since the signal handler tries to
        # redraw the screen before it has even been initialized..
        self.gui.fontsizeWidget.setCurrentIndex(3) # 10
        self.gui.fontsizeWidget.setToolTip("Font size for the treeset editor.")
        self.gui.toolBar.addWidget(self.gui.fontsizeWidget)


    def setWidgetDefaults(self):
        #Done when all signals are set up
        self.gui.treeWidget.setContext(u"editor")
        self.gui.treeWidget.setFontSize(self.gui.fontsizeWidget.currentText())
        self.gui.timeoutWidget.setCurrentIndex(2) #1:00
 
    def currTSet(self):
        if self.currentTreesetIdx==None:
            return None
        else:
            return self.treeSets[self.currentTreesetIdx]

    def setupSignals(self):
        assert QObject.connect(self.gui.actionFirst,SIGNAL("triggered()"),self,SLOT("first()"))
        assert QObject.connect(self.gui.actionPrevious,SIGNAL("triggered()"),self,SLOT("previous()"))
        assert QObject.connect(self.gui.actionNext,SIGNAL("triggered()"),self,SLOT("next()"))
        assert QObject.connect(self.gui.actionLast,SIGNAL("triggered()"),self,SLOT("last()"))
        assert QObject.connect(self.gui.actionOpenFile,SIGNAL("triggered()"),self,SLOT("openFiles()"))
        assert QObject.connect(self.gui.actionOpenFolder,SIGNAL("triggered()"),self,SLOT("openFolder()"))
        assert QObject.connect(self.gui.actionSave,SIGNAL("triggered()"),self,SLOT("save()"))
        assert QObject.connect(self.gui.actionSaveall,SIGNAL("triggered()"),self,SLOT("saveAll()"))
        assert QObject.connect(self.gui.actionSearch,SIGNAL("triggered()"),self,SLOT("openSearch()"))
        assert QObject.connect(self.gui.actionQuit,SIGNAL("triggered()"),self,SLOT("close()"))
        assert QObject.connect(self.gui.actionHelp,SIGNAL("triggered()"),self,SLOT("showHelp()"))
        assert QObject.connect(self.gui.actionAbout,SIGNAL("triggered()"),self,SLOT("showAbout()"))
        assert QObject.connect(self.gui.actionText_editing,SIGNAL("toggled(bool)"),self,SLOT("textEditToggled(bool)"))
        assert QObject.connect(self.gui.actionGotoTree,SIGNAL("triggered()"),self,SLOT("gotoTreeAction()"))
        assert QObject.connect(self.gui.actionStartEditTiming,SIGNAL("triggered()"),self,SLOT("startEditTimingAction()"))
        assert QObject.connect(self.gui.actionStopEditTiming,SIGNAL("triggered()"),self,SLOT("stopEditTimingAction()"))
        assert QObject.connect(self.gui.actionStopAtLastEdit,SIGNAL("triggered()"),self,SLOT("stopTimingAtLastEditAction()"))
        assert QObject.connect(self.gui.actionUnflagAllDeps,SIGNAL("triggered()"),self,SLOT("unflagAllDepsAction()"))
        assert QObject.connect(self.gui.actionDeleteAllFlaggedDeps,SIGNAL("triggered()"),self,SLOT("deleteAllFlaggedDepsAction()"))
        assert QObject.connect(self.gui.halfSecondTimer,SIGNAL("timeout()"),self,SLOT("updateEditTimeInfo()"))

        assert QObject.connect(self.gui.timeoutWidget,SIGNAL("currentIndexChanged(QString)"),self,SLOT("timeoutChanged(QString)"))

        assert QObject.connect(self.gui.fontsizeWidget,SIGNAL("currentIndexChanged(QString)"),self,SLOT("fontsizeChanged(QString)"))

    @pyqtSignature("int")
    def goto(self,idx,startTimer=True):
        if idx<0 or idx>=len(self.currTSet()):
            return
        if self.currTSet()!=None and self.currTSet().currentTreeIdx!=None: #we have a current sentence
            prevSent=self.currTSet()[self.currTSet().currentTreeIdx]
            prevSent.stopEditing()
            QObject.disconnect(prevSent.qtProxy,SIGNAL("editingStarted()"),self,SLOT("editingStarted()"))
            QObject.disconnect(prevSent.qtProxy,SIGNAL("editingStopped()"),self,SLOT("editingStopped()"))
        self.currTSet().currentTreeIdx=idx
        currSent=self.currTSet()[self.currTSet().currentTreeIdx]
        self.gui.treeWidget.setModel(currSent)
        QObject.connect(currSent.qtProxy,SIGNAL("editingStarted()"),self,SLOT("editingStarted()"))
        QObject.connect(currSent.qtProxy,SIGNAL("editingStopped()"),self,SLOT("editingStopped()"))
        if startTimer:
            currSent.startEditing()
        self.gui.progressBar.setValue(idx+1)


    @pyqtSignature("bool")
    def textEditToggled(self,newStatus):
        opt.setup["textEdit"]=newStatus
        if self.currTSet()!=None:
            self.goto(self.currTSet().currentTreeIdx) #should regenerate the context menus

    @pyqtSignature("")
    def first(self):
        self.goto(0)
        
    @pyqtSignature("")
    def previous(self):
        self.goto(self.currTSet().currentTreeIdx-1)

    @pyqtSignature("")
    def next(self):
        self.goto(self.currTSet().currentTreeIdx+1)

    @pyqtSignature("")
    def last(self):
        self.goto(len(self.currTSet())-1)

    @pyqtSignature("")
    def editingStopped(self): #We get this one from the current sentence
        self.gui.actionStartEditTiming.setEnabled(True)
        self.gui.actionStopEditTiming.setDisabled(True)
        self.gui.actionStopAtLastEdit.setDisabled(True)

    @pyqtSignature("")
    def editingStarted(self): #We get this one from the current sentence
        self.gui.actionStartEditTiming.setDisabled(True)
        self.gui.actionStopEditTiming.setEnabled(True)
        self.gui.actionStopAtLastEdit.setEnabled(True)


    @pyqtSignature("")
    def startEditTimingAction(self):
        currentTree=self.currTSet()[self.currTSet().currentTreeIdx]
        currentTree.startEditing()

    @pyqtSignature("")
    def stopEditTimingAction(self):
        currentTree=self.currTSet()[self.currTSet().currentTreeIdx]
        currentTree.stopEditing()

    @pyqtSignature("")
    def stopTimingAtLastEditAction(self):
        currentTree=self.currTSet()[self.currTSet().currentTreeIdx]
        currentTree.stopEditing(currentTree.lastEditTime)


    @pyqtSignature("")
    def updateEditTimeInfo(self):
        if not self.currTSet():
            return
        currentTree=self.currTSet()[self.currTSet().currentTreeIdx]
        editTime=currentTree.editTimeInfo()
        editTimeStr="%02d:%02d"%(editTime.seconds//60,editTime.seconds%60)
        if currentTree.userInactive():
            editTimeStr='<font color="#FF0000">'+editTimeStr+"</font>"
        else:
            editTimeStr='<font color="#000000">'+editTimeStr+"</font>"
        self.gui.editTimeElapsedLabel.setText(editTimeStr)

    @pyqtSignature("")
    def gotoTreeAction(self):
        if self.currTSet()==None:
            return
        idx, ok=QInputDialog.getInteger(self,"Goto tree by number","Give tree number (1-%d)"%len(self.currTSet()), 1, 1, len(self.currTSet()))
        if ok and idx-1!=self.currTSet().currentTreeIdx:
            self.goto(idx-1)

    @pyqtSignature("")
    def unflagAllDepsAction(self):
        if self.currTSet()!=None and self.currTSet().currentTreeIdx!=None: #we have a current sentence
            prevSent=self.currTSet()[self.currTSet().currentTreeIdx]
            prevSent.editUnflagAllDeps(u"editor")
            
    @pyqtSignature("")
    def deleteAllFlaggedDepsAction(self):
        if self.currTSet()!=None and self.currTSet().currentTreeIdx!=None: #we have a current sentence
            prevSent=self.currTSet()[self.currTSet().currentTreeIdx]
            if QMessageBox.question(self,"About to delete all flagged dependencies","Are you sure you want to delete all flagged dependencies?","Don't delete","Delete")==1:
                prevSent.deleteAllFlaggedDeps(tokens=None,context=u"editor")
        

    @pyqtSignature("")
    def openFiles(self,files2open=None):
        if files2open==None:
            files2open=QFileDialog.getOpenFileNames(self, "Open new treeset file(s)", "", TreeSetEditor.openFileFilenameFilter)
            files2open=[unicode(f.toUtf8(),"utf-8") for f in files2open]

        files2open=[os.path.abspath(x) for x in files2open] #Always handle all files by their absolute path
        files2open.sort(cmp=lambda a,b:cmp(os.path.basename(a),os.path.basename(b)))
        progress=QProgressDialog("Opening %d files..."%len(files2open), "Stop", 0, len(files2open), self);
        progress.setWindowModality(Qt.WindowModal);
        #progress.setRange(1,len(files2open))
        counter=0
        for f in files2open:
            try:
                self.openFileByName(f,False)
            except:
                traceback.print_exc()
                raise
            counter+=1
            progress.setValue(counter)
            if progress.wasCanceled():
                break
        self.searchDirty=True
        self.changeTreeset(len(self.treeSets)-1)
        

#         for f in fileNames:
#             fUnicode=unicode(f.toUtf8(),"utf-8")
#             self.openFileByName(fUnicode)
#         print "Initializing search"
#         swisearch.initSearch(self.treeSets)

    @pyqtSignature("")
    def openFolder(self):
        dirName=QFileDialog.getExistingDirectory(self, "Select directory with xml files to open")
        if not dirName:
            return
        else:
            dirName=unicode(dirName.toUtf8(),"utf-8")
        files2open=[]
        filterRe=re.compile(ur".*\.xml$",re.U)
        for root,dirs,files in os.walk(dirName):
            for fName in files:
                if filterRe.match(fName):
                    files2open.append(root+"/"+fName)
        files2open.sort()
        self.openFiles(files2open)


    @pyqtSignature("QString")
    def timeoutChanged(self,newTimeout):
        min,sec=newTimeout.split(":")
        min,sec=int(min),int(sec)
        TreeQ.maxEditInactivity=datetime.timedelta(seconds=60*min+sec)
        
    
    def openBySubdir(self,dirName,filter=r".*\.xml$"):
        files2open=[]
        filterRe=re.compile(filter)
        for root,dirs,files in os.walk(dirName):
            for fName in files:
                if filterRe.match(fName):
                    files2open.append(root+"/"+fName)
        return files2open



        fileName=QFileDialog.getOpenFileName(self, "Open new treeset file", "","*.xml")
        self.openFileByName(fileName)


    @pyqtSignature("QString")
    def fontsizeChanged(self,newFontSize):
        self.gui.treeWidget.setFontSize(newFontSize)
        self.gui.treeWidget.modelChanged()


    @pyqtSignature("")
    def save(self):
        self.currTSet().save()

    @pyqtSignature("PyQt_PyObject")
    def gotoTreeObj(self,tree):
        """Called by the "displayInEditor" menu item of a
        dtreewidget. Asks to move to this tree in the editor"""
        #switch treeset
        self.switchTreeset(tree.treeset.fileName)#This really shouldn't fail, so let any exception propagate
        treeIdx=tree.treeset.sentences.index(tree) #...same here
        self.goto(treeIdx)

    @pyqtSignature("PyQt_PyObject")
    def treesetDirty(self,fileName):
        """Treesets trigger this one and pass their name"""
        self.searchDirty=True
        if self.currTSet().fileName==fileName:
            if not self.windowTitle().startsWith("*"):
                self.setWindowTitle("*"+self.windowTitle())
            self.gui.actionSave.setEnabled(True)
            #Update also the counter (needed ever since sentence splitting was added, so the number of sentences can change on the fly)
            if self.gui.progressBar.maximum()!=len(self.currTSet()):
                self.gui.progressBar.setMaximum(len(self.currTSet()))
                self.gui.progressBar.repaint()
            


    @pyqtSignature("PyQt_PyObject")
    def treesetClean(self,fileName):
        """Treesets trigger this one and pass their name"""
        if self.currTSet().fileName==fileName:
            if self.windowTitle().startsWith("*"):
                self.setWindowTitle(self.windowTitle()[1:])
            self.gui.actionSave.setEnabled(False)


    @pyqtSignature("PyQt_PyObject")
    def switchTreeset(self,fileName):
        """treeset menu actions trigger this one"""
        for tsetIdx,tSet in enumerate(self.treeSets):
            if tSet.fileName==fileName:
                self.changeTreeset(tsetIdx)
                return
        assert False


    @pyqtSignature("")
    def saveAll(self):
        for tSet in self.treeSets:
            if tSet.dirty:
                tSet.save()

    def initSearchIfDirty(self):
        indices=[idx for idx,tset in enumerate(self.treeSets) if tset.searchDirty] #dirty treesets
        #.searchDirty is defined in TreeSetQ!
        if not indices:
            return
        swisearch.initSearch(self.treeSets,indices,True)
        for tset in self.treeSets:
            tset.searchDirty=False

    @pyqtSignature("")
    def openSearch(self):
#         if self.currTSet()!=None and self.currTSet().currentTreeIdx!=None: #we have a current sentence
#             currSent=self.currTSet()[self.currTSet().currentTreeIdx]
#             currSent.stopEditing()
        self.initSearchIfDirty()
        f=TreeSearchForm(self.treeSets,self,self,False)
        f.show()

    def changeTreeset(self,newIdx):
        assert newIdx>=0 and newIdx<len(self.treeSets)
        if self.currTSet()!=None and self.currTSet().currentTreeIdx!=None: #we have a current sentence
            prevSent=self.currTSet()[self.currTSet().currentTreeIdx]
            prevSent.stopEditing()
            QObject.disconnect(prevSent.qtProxy,SIGNAL("editingStarted()"),self,SLOT("editingStarted()"))
            QObject.disconnect(prevSent.qtProxy,SIGNAL("editingStopped()"),self,SLOT("editingStopped()"))
        self.currentTreesetIdx=newIdx
        self.setWindowTitle(self.currTSet().fileName)
        self.gui.progressBar.setMinimum(0)
        self.gui.progressBar.setMaximum(len(self.currTSet()))
        self.gui.progressBar.repaint()

        if self.currTSet().currentTreeIdx!=None:
            self.goto(self.currTSet().currentTreeIdx,startTimer=False)
        else:
            self.goto(0,startTimer=False)
        self.currTSet().announceStatus() #Make the treeset announce clean/dirty by sending the appropriate signal
    
    def openFileByName(self,fileName,changeTo=True):
        #1) look whether the file is open already
        for tsetIdx,tSet in enumerate(self.treeSets):
            if tSet.fileName==fileName:
                self.changeTreeset(tsetIdx)
                return
        newTSet=TreeSetQ.fromFile(fileName)
        assert self.connect(newTSet.qtProxy,SIGNAL("treesetDirty(PyQt_PyObject)"),self,SLOT("treesetDirty(PyQt_PyObject)"))
        assert self.connect(newTSet.qtProxy,SIGNAL("treesetClean(PyQt_PyObject)"),self,SLOT("treesetClean(PyQt_PyObject)"))
        self.treeSets.append(newTSet)
        newAction=FileNameAction(fileName,self.gui.menuTreeset)
        assert self.connect(newAction,SIGNAL("selectedFileName(PyQt_PyObject)"),self,SLOT("switchTreeset(PyQt_PyObject)"))
        assert self.connect(newTSet.qtProxy,SIGNAL("treesetDirty(PyQt_PyObject)"),newAction,SLOT("treesetDirty(PyQt_PyObject)"))
        assert self.connect(newTSet.qtProxy,SIGNAL("treesetClean(PyQt_PyObject)"),newAction,SLOT("treesetClean(PyQt_PyObject)"))
        self.gui.menuTreeset.addAction(newAction)
        if changeTo:
            self.changeTreeset(len(self.treeSets)-1)

    @pyqtSignature("")
    def showHelp(self):
        hf=HelpForm(self)
        hf.show()

    @pyqtSignature("")
    def showAbout(self):
        af=AboutForm(self)
        af.show()


    def closeEvent(self,e):
        if self.currTSet()!=None and self.currTSet().currentTreeIdx!=None: #we have a current sentence
            prevSent=self.currTSet()[self.currTSet().currentTreeIdx]
            prevSent.stopEditing()

        #One needs to check whether all files are saved
        dirtyTSets=[t for t in self.treeSets if t.dirty]
        if not dirtyTSets:
            #we're good
            return
        #There are dirty tree-sets, ask the user what to do
        if len(dirtyTSets)==1:
            q="You have one unsaved treeset."
        else:
            q="You have %d unsaved treesets."%len(dirtyTSets)
        answer=QMessageBox.warning(self,"Unsaved treeset warning",q,"Save all treesets","Cancel","Quit without saving",0,1)
        if answer==0:
            for t in dirtyTSets:
                t.save()
        elif answer==1:
            e.ignore()
        
    def keyPressEvent(self, e):
        # Font size changed
        if e.key()==Qt.Key_Plus:
            newIdx=self.gui.fontsizeWidget.currentIndex()+1
            if newIdx<self.gui.fontsizeWidget.count():
                self.gui.fontsizeWidget.setCurrentIndex(newIdx)
        elif e.key()==Qt.Key_Minus:
            newIdx=self.gui.fontsizeWidget.currentIndex()-1
            if newIdx>=0:
                self.gui.fontsizeWidget.setCurrentIndex(newIdx)
            

