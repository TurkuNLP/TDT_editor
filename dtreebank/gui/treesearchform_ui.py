# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'treesearchform.ui'
#
# Created: Tue Feb  7 15:24:41 2017
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

class Ui_TreeSearchForm(object):
    def setupUi(self, TreeSearchForm):
        TreeSearchForm.setObjectName(_fromUtf8("TreeSearchForm"))
        TreeSearchForm.resize(1270, 846)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(TreeSearchForm.sizePolicy().hasHeightForWidth())
        TreeSearchForm.setSizePolicy(sizePolicy)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/babelfish.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        TreeSearchForm.setWindowIcon(icon)
        self.vboxlayout = QtGui.QVBoxLayout(TreeSearchForm)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.frame = QtGui.QFrame(TreeSearchForm)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.frame.setFrameShape(QtGui.QFrame.NoFrame)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.gridlayout = QtGui.QGridLayout(self.frame)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.groupBox = QtGui.QGroupBox(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.groupBox.setFlat(False)
        self.groupBox.setCheckable(False)
        self.groupBox.setChecked(False)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridlayout1 = QtGui.QGridLayout(self.groupBox)
        self.gridlayout1.setObjectName(_fromUtf8("gridlayout1"))
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridlayout1.addWidget(self.label_4, 0, 0, 1, 1)
        self.doSearchButton = QtGui.QPushButton(self.groupBox)
        self.doSearchButton.setAutoDefault(True)
        self.doSearchButton.setDefault(True)
        self.doSearchButton.setObjectName(_fromUtf8("doSearchButton"))
        self.gridlayout1.addWidget(self.doSearchButton, 0, 2, 1, 1)
        self.caseSensitive = QtGui.QCheckBox(self.groupBox)
        self.caseSensitive.setObjectName(_fromUtf8("caseSensitive"))
        self.gridlayout1.addWidget(self.caseSensitive, 1, 1, 1, 1)
        self.depExpression = QtGui.QComboBox(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.depExpression.sizePolicy().hasHeightForWidth())
        self.depExpression.setSizePolicy(sizePolicy)
        self.depExpression.setEditable(True)
        self.depExpression.setInsertPolicy(QtGui.QComboBox.InsertAtTop)
        self.depExpression.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.depExpression.setObjectName(_fromUtf8("depExpression"))
        self.gridlayout1.addWidget(self.depExpression, 0, 1, 1, 1)
        self.gridlayout.addWidget(self.groupBox, 0, 0, 1, 1)
        self.groupBox_2 = QtGui.QGroupBox(self.frame)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox_2)
        self.vboxlayout1.setObjectName(_fromUtf8("vboxlayout1"))
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        self.label = QtGui.QLabel(self.groupBox_2)
        self.label.setObjectName(_fromUtf8("label"))
        self.hboxlayout.addWidget(self.label)
        self.infoMatchingTokens = QtGui.QLabel(self.groupBox_2)
        self.infoMatchingTokens.setObjectName(_fromUtf8("infoMatchingTokens"))
        self.hboxlayout.addWidget(self.infoMatchingTokens)
        spacerItem = QtGui.QSpacerItem(21, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.label_3 = QtGui.QLabel(self.groupBox_2)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.hboxlayout.addWidget(self.label_3)
        self.infoMatchingTrees = QtGui.QLabel(self.groupBox_2)
        self.infoMatchingTrees.setObjectName(_fromUtf8("infoMatchingTrees"))
        self.hboxlayout.addWidget(self.infoMatchingTrees)
        spacerItem1 = QtGui.QSpacerItem(21, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem1)
        self.label_6 = QtGui.QLabel(self.groupBox_2)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.hboxlayout.addWidget(self.label_6)
        self.infoMatchingTreesets = QtGui.QLabel(self.groupBox_2)
        self.infoMatchingTreesets.setObjectName(_fromUtf8("infoMatchingTreesets"))
        self.hboxlayout.addWidget(self.infoMatchingTreesets)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem2)
        self.vboxlayout1.addLayout(self.hboxlayout)
        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setObjectName(_fromUtf8("hboxlayout1"))
        self.label_8 = QtGui.QLabel(self.groupBox_2)
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.hboxlayout1.addWidget(self.label_8)
        self.infoPrologExpr = QtGui.QLineEdit(self.groupBox_2)
        self.infoPrologExpr.setObjectName(_fromUtf8("infoPrologExpr"))
        self.hboxlayout1.addWidget(self.infoPrologExpr)
        self.vboxlayout1.addLayout(self.hboxlayout1)
        self.gridlayout.addWidget(self.groupBox_2, 1, 0, 1, 1)
        self.vboxlayout.addWidget(self.frame)
        self.resultScrollArea = QtGui.QScrollArea(TreeSearchForm)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.resultScrollArea.sizePolicy().hasHeightForWidth())
        self.resultScrollArea.setSizePolicy(sizePolicy)
        self.resultScrollArea.setFrameShape(QtGui.QFrame.StyledPanel)
        self.resultScrollArea.setFrameShadow(QtGui.QFrame.Raised)
        self.resultScrollArea.setObjectName(_fromUtf8("resultScrollArea"))
        self.vboxlayout.addWidget(self.resultScrollArea)

        self.retranslateUi(TreeSearchForm)
        QtCore.QMetaObject.connectSlotsByName(TreeSearchForm)
        TreeSearchForm.setTabOrder(self.depExpression, self.doSearchButton)
        TreeSearchForm.setTabOrder(self.doSearchButton, self.caseSensitive)
        TreeSearchForm.setTabOrder(self.caseSensitive, self.resultScrollArea)
        TreeSearchForm.setTabOrder(self.resultScrollArea, self.infoPrologExpr)

    def retranslateUi(self, TreeSearchForm):
        TreeSearchForm.setWindowTitle(_translate("TreeSearchForm", "Search", None))
        self.groupBox.setTitle(_translate("TreeSearchForm", "Search criteria", None))
        self.label_4.setText(_translate("TreeSearchForm", "Expression", None))
        self.doSearchButton.setText(_translate("TreeSearchForm", "Go", None))
        self.caseSensitive.setText(_translate("TreeSearchForm", "Case sensitive", None))
        self.groupBox_2.setTitle(_translate("TreeSearchForm", "Search information", None))
        self.label.setText(_translate("TreeSearchForm", "Matching tokens:", None))
        self.infoMatchingTokens.setText(_translate("TreeSearchForm", "N/A", None))
        self.label_3.setText(_translate("TreeSearchForm", "Matching trees:", None))
        self.infoMatchingTrees.setText(_translate("TreeSearchForm", "N/A", None))
        self.label_6.setText(_translate("TreeSearchForm", "Matching treesets:", None))
        self.infoMatchingTreesets.setText(_translate("TreeSearchForm", "N/A", None))
        self.label_8.setText(_translate("TreeSearchForm", "Prolog expression used:", None))

import resfile_rc
