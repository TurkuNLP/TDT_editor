from dtreebank.gui.treesearchform_ui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
import os
from dtreebank.core.treeset import *
from dtreebank.gui.dtreewidget import *
import os.path
import codecs
import re

import xml.etree.cElementTree as ET

import dtreebank.core.search.swisearch2 as swisearch
from dtreebank.core.search.searchexpression import ExpressionError

#This is the search dialog

class TreeSearchForm(QDialog):

    def __init__(self,treesets,parentEditor=None,parent=None,readOnly=False):
        QWidget.__init__(self,parent,Qt.Window)
        self.treesets=treesets #these treesets will be searched
        self.gui=Ui_TreeSearchForm()
        self.gui.setupUi(self)
        self.setupSignals()
        self.resultFrame=None
        self.popularSearches=[]
        self.parentEditor=parentEditor
        self.readOnly=readOnly

        #Fill in the search form
        DIR=os.path.dirname(os.path.abspath(__file__))
        searches=codecs.open(os.path.join(DIR,"popularSearches"),"rt","utf-8")
        for line in searches:
            line=line.strip()
            if not line:
                continue
            self.popularSearches.append(line)
        searches.close()
        for s in self.popularSearches[::-1]:
            if s.startswith(u"---"):
                self.gui.depExpression.insertSeparator(0)
            else:
                self.gui.depExpression.insertItem(0,QString(s))
        self.gui.depExpression.setAutoCompletion(False)
        self.gui.depExpression.setCurrentIndex(-1)
        

    def setupSignals(self):
        assert QObject.connect(self.gui.doSearchButton,SIGNAL("clicked()"),self,SLOT("doSearchSWI()"))

 
    @pyqtSignature("")
    def doSearchSWI(self):
        self.parentEditor.initSearchIfDirty()
        if self.resultFrame:
            self.resultFrame.setParent(None)
            self.resultFrame=None
        self.resultFrame=QFrame(self.gui.resultScrollArea)
        self.gui.resultScrollArea.setWidget(self.resultFrame)
        layout=QVBoxLayout(self.resultFrame)
        self.resultFrame.setLayout(layout)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        layout.setSpacing(0)


        try:
            if self.gui.caseSensitive.checkState()==Qt.Checked:
                caseSensitive=True
            else:
                caseSensitive=False
            searchExpr=unicode(self.gui.depExpression.currentText())
            print >> sys.stderr, "Search expression:", searchExpr.encode("utf-8")
            lst,usedExpression=swisearch.doSearch(unicode(self.gui.depExpression.currentText()),caseSensitive=caseSensitive)
            self.gui.infoPrologExpr.setText(usedExpression)
            #Okay, this went well, so insert the expression into the combo box unless it's there
            for idx in range(self.gui.depExpression.count()):
                if unicode(self.gui.depExpression.itemText(idx))==searchExpr:
                    break
            else:
                self.gui.depExpression.insertItem(0,QString(searchExpr))
        except ExpressionError, e:
            QMessageBox.critical(self,"Invalid search expression",u"The search expression was not valid:\n\n"+e.message,QMessageBox.Ok,QMessageBox.NoButton)
            return
        
        print >> sys.stderr, "Prolog done"

        #Now do the counting:
        matchedTreesets=len(set(match[0] for match in lst))
        totalTreesets=len(self.treesets)
        matchedTrees=len(set((match[0],match[1]) for match in lst))
        totalTrees=sum(len(tset.sentences) for tset in self.treesets)
        matchedTokens=sum(len(match[2]) for match in lst)
        totalTokens=sum(len(tree.tokens) for tset in self.treesets for tree in tset.sentences)
        self.gui.infoMatchingTreesets.setText("%d/%d"%(matchedTreesets,totalTreesets))
        self.gui.infoMatchingTrees.setText("%d/%d"%(matchedTrees,totalTrees))
        self.gui.infoMatchingTokens.setText("%d/%d"%(matchedTokens,totalTokens))

        progress=QProgressDialog("Drawing %d trees..."%len(lst), "Stop", 0, len(lst), self);
        progress.setWindowModality(Qt.WindowModal);
        progress.setRange(1,len(lst))
        counter=0
        for tsetIdx,tIdx,matchlist in lst:
            sentence=self.treesets[tsetIdx].sentences[tIdx]
            matchingTokens=set(matchlist)
            matchingDeps=set()
            newW=DTreeWidget(self.resultFrame,u"searchform",self.readOnly)
            if self.parentEditor!=None:
                QObject.connect(newW,SIGNAL("gotoTreeObj(PyQt_PyObject)"),self.parentEditor,SLOT("gotoTreeObj(PyQt_PyObject)"))
            newW.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
            newW.setModel(sentence,set(matchingTokens),set(matchingDeps))
            layout.addWidget(newW,Qt.AlignLeft)
            counter+=1
            progress.setValue(counter)
            if progress.wasCanceled():
                break
            

