from dtreebank.gui.aboutform_ui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class AboutForm(QWidget):

    def __init__(self,parent=None):
        QWidget.__init__(self,parent,Qt.Window)
        self.gui=Ui_AboutForm()
        self.gui.setupUi(self)
        self.gui.textBrowser.setSource(QUrl("treeseteditorabout.html"))
