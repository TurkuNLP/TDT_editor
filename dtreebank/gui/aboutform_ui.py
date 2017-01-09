# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'aboutform.ui'
#
# Created: Mon Jan  9 14:19:10 2017
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_AboutForm(object):
    def setupUi(self, AboutForm):
        AboutForm.setObjectName(_fromUtf8("AboutForm"))
        AboutForm.resize(400, 300)
        self.hboxlayout = QtGui.QHBoxLayout(AboutForm)
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        self.textBrowser = QtGui.QTextBrowser(AboutForm)
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))
        self.hboxlayout.addWidget(self.textBrowser)

        self.retranslateUi(AboutForm)
        QtCore.QMetaObject.connectSlotsByName(AboutForm)

    def retranslateUi(self, AboutForm):
        AboutForm.setWindowTitle(_translate("AboutForm", "Help", None))

