# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'treeseteditor.ui'
#
# Created: Tue Feb  7 15:24:40 2017
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

class Ui_TreeSetEditor(object):
    def setupUi(self, TreeSetEditor):
        TreeSetEditor.setObjectName(_fromUtf8("TreeSetEditor"))
        TreeSetEditor.resize(872, 383)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/babelfish.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        TreeSetEditor.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(TreeSetEditor)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.vboxlayout = QtGui.QVBoxLayout(self.centralwidget)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        spacerItem = QtGui.QSpacerItem(421, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.progressBar = QtGui.QProgressBar(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progressBar.sizePolicy().hasHeightForWidth())
        self.progressBar.setSizePolicy(sizePolicy)
        self.progressBar.setMaximum(0)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.progressBar.setTextVisible(True)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.hboxlayout.addWidget(self.progressBar)
        self.vboxlayout.addLayout(self.hboxlayout)
        self.treeWidget = DTreeWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeWidget.sizePolicy().hasHeightForWidth())
        self.treeWidget.setSizePolicy(sizePolicy)
        self.treeWidget.setObjectName(_fromUtf8("treeWidget"))
        self.vboxlayout.addWidget(self.treeWidget)
        TreeSetEditor.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(TreeSetEditor)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 872, 27))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuNavigation = QtGui.QMenu(self.menubar)
        self.menuNavigation.setObjectName(_fromUtf8("menuNavigation"))
        self.menuTreeset = TreeSetMenu(self.menubar)
        self.menuTreeset.setObjectName(_fromUtf8("menuTreeset"))
        self.menuSearch = QtGui.QMenu(self.menubar)
        self.menuSearch.setObjectName(_fromUtf8("menuSearch"))
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName(_fromUtf8("menuHelp"))
        self.menuConfig = QtGui.QMenu(self.menubar)
        self.menuConfig.setObjectName(_fromUtf8("menuConfig"))
        TreeSetEditor.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(TreeSetEditor)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        TreeSetEditor.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(TreeSetEditor)
        self.toolBar.setIconSize(QtCore.QSize(16, 16))
        self.toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.toolBar.setFloatable(False)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        TreeSetEditor.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.timeBar = QtGui.QToolBar(TreeSetEditor)
        self.timeBar.setObjectName(_fromUtf8("timeBar"))
        TreeSetEditor.addToolBar(QtCore.Qt.TopToolBarArea, self.timeBar)
        TreeSetEditor.insertToolBarBreak(self.timeBar)
        self.actionPrevious = QtGui.QAction(TreeSetEditor)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/1leftarrow.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPrevious.setIcon(icon1)
        self.actionPrevious.setObjectName(_fromUtf8("actionPrevious"))
        self.actionNext = QtGui.QAction(TreeSetEditor)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/1rightarrow.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionNext.setIcon(icon2)
        self.actionNext.setObjectName(_fromUtf8("actionNext"))
        self.actionFirst = QtGui.QAction(TreeSetEditor)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/2leftarrow.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionFirst.setIcon(icon3)
        self.actionFirst.setObjectName(_fromUtf8("actionFirst"))
        self.actionLast = QtGui.QAction(TreeSetEditor)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/2rightarrow.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionLast.setIcon(icon4)
        self.actionLast.setObjectName(_fromUtf8("actionLast"))
        self.actionSave = QtGui.QAction(TreeSetEditor)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/filesave.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave.setIcon(icon5)
        self.actionSave.setObjectName(_fromUtf8("actionSave"))
        self.actionOpenFile = QtGui.QAction(TreeSetEditor)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/filesopen.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionOpenFile.setIcon(icon6)
        self.actionOpenFile.setObjectName(_fromUtf8("actionOpenFile"))
        self.actionClose = QtGui.QAction(TreeSetEditor)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/fileclose.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionClose.setIcon(icon7)
        self.actionClose.setObjectName(_fromUtf8("actionClose"))
        self.actionSaveall = QtGui.QAction(TreeSetEditor)
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/save_all.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSaveall.setIcon(icon8)
        self.actionSaveall.setObjectName(_fromUtf8("actionSaveall"))
        self.actionSearch = QtGui.QAction(TreeSetEditor)
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/search.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSearch.setIcon(icon9)
        self.actionSearch.setObjectName(_fromUtf8("actionSearch"))
        self.actionOpenFolder = QtGui.QAction(TreeSetEditor)
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/foldopen.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionOpenFolder.setIcon(icon10)
        self.actionOpenFolder.setObjectName(_fromUtf8("actionOpenFolder"))
        self.actionQuit = QtGui.QAction(TreeSetEditor)
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/exit.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionQuit.setIcon(icon11)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))
        self.actionHelp = QtGui.QAction(TreeSetEditor)
        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/help.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionHelp.setIcon(icon12)
        self.actionHelp.setObjectName(_fromUtf8("actionHelp"))
        self.actionAbout = QtGui.QAction(TreeSetEditor)
        self.actionAbout.setObjectName(_fromUtf8("actionAbout"))
        self.actionText_editing = QtGui.QAction(TreeSetEditor)
        self.actionText_editing.setCheckable(True)
        self.actionText_editing.setObjectName(_fromUtf8("actionText_editing"))
        self.actionGotoTree = QtGui.QAction(TreeSetEditor)
        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/goto.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionGotoTree.setIcon(icon13)
        self.actionGotoTree.setObjectName(_fromUtf8("actionGotoTree"))
        self.actionStartEditTiming = QtGui.QAction(TreeSetEditor)
        icon14 = QtGui.QIcon()
        icon14.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/player_play.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionStartEditTiming.setIcon(icon14)
        self.actionStartEditTiming.setObjectName(_fromUtf8("actionStartEditTiming"))
        self.actionStopEditTiming = QtGui.QAction(TreeSetEditor)
        icon15 = QtGui.QIcon()
        icon15.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/player_stop.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionStopEditTiming.setIcon(icon15)
        self.actionStopEditTiming.setObjectName(_fromUtf8("actionStopEditTiming"))
        self.actionStopAtLastEdit = QtGui.QAction(TreeSetEditor)
        icon16 = QtGui.QIcon()
        icon16.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/player_rew.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionStopAtLastEdit.setIcon(icon16)
        self.actionStopAtLastEdit.setObjectName(_fromUtf8("actionStopAtLastEdit"))
        self.actionUnflagAllDeps = QtGui.QAction(TreeSetEditor)
        icon17 = QtGui.QIcon()
        icon17.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/apply.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionUnflagAllDeps.setIcon(icon17)
        self.actionUnflagAllDeps.setObjectName(_fromUtf8("actionUnflagAllDeps"))
        self.actionDeleteAllFlaggedDeps = QtGui.QAction(TreeSetEditor)
        icon18 = QtGui.QIcon()
        icon18.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/icons/trash.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionDeleteAllFlaggedDeps.setIcon(icon18)
        self.actionDeleteAllFlaggedDeps.setObjectName(_fromUtf8("actionDeleteAllFlaggedDeps"))
        self.menuFile.addAction(self.actionOpenFile)
        self.menuFile.addAction(self.actionOpenFolder)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveall)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menuNavigation.addAction(self.actionFirst)
        self.menuNavigation.addAction(self.actionPrevious)
        self.menuNavigation.addAction(self.actionNext)
        self.menuNavigation.addAction(self.actionLast)
        self.menuNavigation.addAction(self.actionGotoTree)
        self.menuSearch.addAction(self.actionSearch)
        self.menuHelp.addAction(self.actionHelp)
        self.menuHelp.addAction(self.actionAbout)
        self.menuConfig.addAction(self.actionText_editing)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuNavigation.menuAction())
        self.menubar.addAction(self.menuSearch.menuAction())
        self.menubar.addAction(self.menuConfig.menuAction())
        self.menubar.addAction(self.menuTreeset.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.toolBar.addAction(self.actionOpenFile)
        self.toolBar.addAction(self.actionOpenFolder)
        self.toolBar.addAction(self.actionSave)
        self.toolBar.addAction(self.actionSaveall)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionFirst)
        self.toolBar.addAction(self.actionPrevious)
        self.toolBar.addAction(self.actionNext)
        self.toolBar.addAction(self.actionLast)
        self.toolBar.addAction(self.actionGotoTree)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionSearch)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionUnflagAllDeps)
        self.toolBar.addAction(self.actionDeleteAllFlaggedDeps)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionHelp)
        self.toolBar.addSeparator()
        self.timeBar.addAction(self.actionStartEditTiming)
        self.timeBar.addAction(self.actionStopEditTiming)
        self.timeBar.addAction(self.actionStopAtLastEdit)
        self.timeBar.addSeparator()

        self.retranslateUi(TreeSetEditor)
        QtCore.QMetaObject.connectSlotsByName(TreeSetEditor)

    def retranslateUi(self, TreeSetEditor):
        TreeSetEditor.setWindowTitle(_translate("TreeSetEditor", "MainWindow", None))
        self.progressBar.setFormat(_translate("TreeSetEditor", "%v/%m", None))
        self.menuFile.setTitle(_translate("TreeSetEditor", "File", None))
        self.menuNavigation.setTitle(_translate("TreeSetEditor", "Navigation", None))
        self.menuTreeset.setTitle(_translate("TreeSetEditor", "Treeset", None))
        self.menuSearch.setTitle(_translate("TreeSetEditor", "Search", None))
        self.menuHelp.setTitle(_translate("TreeSetEditor", "Help", None))
        self.menuConfig.setTitle(_translate("TreeSetEditor", "Config", None))
        self.toolBar.setWindowTitle(_translate("TreeSetEditor", "toolBar", None))
        self.timeBar.setWindowTitle(_translate("TreeSetEditor", "toolBar_2", None))
        self.actionPrevious.setText(_translate("TreeSetEditor", "Previous", None))
        self.actionNext.setText(_translate("TreeSetEditor", "Next", None))
        self.actionFirst.setText(_translate("TreeSetEditor", "First", None))
        self.actionLast.setText(_translate("TreeSetEditor", "Last", None))
        self.actionSave.setText(_translate("TreeSetEditor", "Save", None))
        self.actionOpenFile.setText(_translate("TreeSetEditor", "Open File(s)", None))
        self.actionClose.setText(_translate("TreeSetEditor", "Close", None))
        self.actionSaveall.setText(_translate("TreeSetEditor", "Save All", None))
        self.actionSearch.setText(_translate("TreeSetEditor", "Search", None))
        self.actionOpenFolder.setText(_translate("TreeSetEditor", "Open Folder", None))
        self.actionQuit.setText(_translate("TreeSetEditor", "Quit", None))
        self.actionHelp.setText(_translate("TreeSetEditor", "Help", None))
        self.actionAbout.setText(_translate("TreeSetEditor", "About", None))
        self.actionText_editing.setText(_translate("TreeSetEditor", "Text editing", None))
        self.actionText_editing.setToolTip(_translate("TreeSetEditor", "Allow token editing and sentence splitting", None))
        self.actionGotoTree.setText(_translate("TreeSetEditor", "gotoTree", None))
        self.actionStartEditTiming.setText(_translate("TreeSetEditor", "StartEditTiming", None))
        self.actionStartEditTiming.setToolTip(_translate("TreeSetEditor", "Start timing", None))
        self.actionStopEditTiming.setText(_translate("TreeSetEditor", "StopEditTiming", None))
        self.actionStopEditTiming.setToolTip(_translate("TreeSetEditor", "Stop timing now", None))
        self.actionStopAtLastEdit.setText(_translate("TreeSetEditor", "stopAtLastEdit", None))
        self.actionStopAtLastEdit.setToolTip(_translate("TreeSetEditor", "Stop timing at last edit time", None))
        self.actionUnflagAllDeps.setText(_translate("TreeSetEditor", "unflagAllDeps", None))
        self.actionUnflagAllDeps.setToolTip(_translate("TreeSetEditor", "Unflag all dependencies", None))
        self.actionDeleteAllFlaggedDeps.setText(_translate("TreeSetEditor", "deleteAllFlaggedDeps", None))
        self.actionDeleteAllFlaggedDeps.setToolTip(_translate("TreeSetEditor", "Delete all flagged dependencies", None))

from dtreewidget import DTreeWidget
from treesetmenu import TreeSetMenu
import resfile_rc
