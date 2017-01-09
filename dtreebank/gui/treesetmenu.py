from PyQt4.QtCore import *
from PyQt4.QtGui import *


class TreeSetMenu(QMenu):

    def __init__(self,parent):
        QMenu.__init__(self,parent)
        self.submenus={} #key: (prefix,series) value: QMenu

    def addAction(self,fileNameAction):
        nameComponents=fileNameAction.getFileNameComponents()
        if nameComponents==None: #this name doesn't have any particular structure, add it as-is
            QMenu.addAction(self,fileNameAction)
        else:
            prefix,number=nameComponents
            series=number//50
            if (prefix,series) in self.submenus:
                menu=self.submenus[(prefix,series)]
            else:
                menu=self.addMenu("%s%d-%d"%(prefix,series*50,series*50+49))
                self.submenus[(prefix,series)]=menu
            menu.addAction(fileNameAction)
