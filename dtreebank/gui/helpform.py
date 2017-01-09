from dtreebank.gui.helpform_ui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class HelpForm(QWidget):

    def __init__(self,parent=None):
        QWidget.__init__(self,parent,Qt.Window)
        self.gui=Ui_HelpForm()
        self.gui.setupUi(self)
        self.gui.textBrowser.setSource(QUrl("treeseteditorhelp.html"))
