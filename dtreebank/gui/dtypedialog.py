from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
import os.path
import options

class TypeButton(QPushButton):

    def __init__(self,dType,parent):
        QPushButton.__init__(self,dType,parent)
        self.parent=parent
        self.dType=dType.replace("&","").lower()
        self.connect(self,SIGNAL("clicked()"),SLOT("clicked()"))
    
    @pyqtSignature("")
    def clicked(self):
        self.parent.selectType(self.dType)

    def keyPressEvent(self,e):
        e.ignore()

class DTypeDialog(QDialog):

    def __init__(self,parent,setName="depTypes",cols=5):
        QDialog.__init__(self,parent)
        DIR=os.path.dirname(os.path.abspath(__file__))
        print options.setup
        depTypes=open(os.path.join(DIR,options.setup["depsFile"]),"rt")
        self.hotkeys={} #key: key value: dType

        self.mainLayout=QGridLayout(self)
        self.selectedType=None #here we store the selected type

        row=0
        col=0
        for depType in depTypes:
            depType=depType.strip()
            if not depType: #emptyLine
                row+=1
                col=0
                #make a line
                self.mainLayout.setRowMinimumHeight(row,10)

                row+=1
                continue
            dotIdx=depType.find(".")
            if dotIdx>=0:
                hotkey=depType[dotIdx+1]
                if hotkey in self.hotkeys:
                    print >> sys.stderr, "%s redefines hotkey '%s', ignoring"%(depType,hotkey)
                    hotkey=None
            else:
                hotkey=None
            
            button=TypeButton(depType.replace(".","&"),self)
            self.mainLayout.addWidget(button,row,col)
            if hotkey:
                self.hotkeys[hotkey]=depType.replace(".","").lower()
            col+=1
            if col==cols:
                col=0
                row+=1
        
        button=QPushButton("Cancel",self)
        self.mainLayout.addWidget(button,row+1,0,1,-1)
        self.connect(button,SIGNAL("clicked()"),SLOT("reject()"))
        

        self.setLayout(self.mainLayout)
        self.setWindowTitle("Select dependency type")
        self.setModal(True)
        
        
    def selectType(self,dType):
        """Called by one of the buttons"""
        self.selectedType=dType
        self.accept()

    def keyPressEvent(self,e):
        k=str(e.text())
        if k in self.hotkeys:
            self.selectType(self.hotkeys[k])
