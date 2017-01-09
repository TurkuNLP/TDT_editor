#!/usr/bin/env python

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys

from dtreebank.gui.treeseteditor import TreeSetEditor

from dtreebank.gui import options
options.parseOptions()
app = QApplication(sys.argv)
TSEditorWidget=TreeSetEditor(options.args)
TSEditorWidget.show()
sys.exit(app.exec_())

