# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QMainWindow, QMenu, QMenuBar,
    QSizePolicy, QStatusBar, QTabWidget, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(910, 692)
        self.actExit = QAction(MainWindow)
        self.actExit.setObjectName(u"actExit")
        self.actResetAll = QAction(MainWindow)
        self.actResetAll.setObjectName(u"actResetAll")
        self.actSaveConfig = QAction(MainWindow)
        self.actSaveConfig.setObjectName(u"actSaveConfig")
        self.actConfigItems = QAction(MainWindow)
        self.actConfigItems.setObjectName(u"actConfigItems")
        self.actViewLog = QAction(MainWindow)
        self.actViewLog.setObjectName(u"actViewLog")
        self.actionDefault = QAction(MainWindow)
        self.actionDefault.setObjectName(u"actionDefault")
        self.actAbout = QAction(MainWindow)
        self.actAbout.setObjectName(u"actAbout")
        self.actGlobalSetting = QAction(MainWindow)
        self.actGlobalSetting.setObjectName(u"actGlobalSetting")
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        self.vlMain = QVBoxLayout(self.centralWidget)
        self.vlMain.setObjectName(u"vlMain")
        self.tabWidget = QTabWidget(self.centralWidget)
        self.tabWidget.setObjectName(u"tabWidget")

        self.vlMain.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralWidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 910, 27))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        self.menu = QMenu(self.menuEdit)
        self.menu.setObjectName(u"menu")
        self.menuAbout = QMenu(self.menubar)
        self.menuAbout.setObjectName(u"menuAbout")
        self.menuSettings = QMenu(self.menubar)
        self.menuSettings.setObjectName(u"menuSettings")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuSettings.menuAction())
        self.menubar.addAction(self.menuAbout.menuAction())
        self.menuFile.addAction(self.actExit)
        self.menuEdit.addAction(self.actResetAll)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actSaveConfig)
        self.menuEdit.addAction(self.menu.menuAction())
        self.menuEdit.addAction(self.actConfigItems)
        self.menu.addAction(self.actionDefault)
        self.menuAbout.addAction(self.actAbout)
        self.menuAbout.addSeparator()
        self.menuAbout.addAction(self.actViewLog)
        self.menuSettings.addAction(self.actGlobalSetting)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actExit.setText(QCoreApplication.translate("MainWindow", u"\u9000\u51fa", None))
        self.actResetAll.setText(QCoreApplication.translate("MainWindow", u"\u91cd\u7f6e\u6240\u6709", None))
        self.actSaveConfig.setText(QCoreApplication.translate("MainWindow", u"\u4fdd\u5b58\u4e3a\u914d\u7f6e", None))
        self.actConfigItems.setText(QCoreApplication.translate("MainWindow", u"\u914d\u7f6e\u9879", None))
        self.actViewLog.setText(QCoreApplication.translate("MainWindow", u"\u67e5\u770b\u65e5\u5fd7", None))
        self.actionDefault.setText(QCoreApplication.translate("MainWindow", u"Default", None))
        self.actAbout.setText(QCoreApplication.translate("MainWindow", u"\u5173\u4e8e\u53ef\u9760\u6027\u5de5\u5177", None))
        self.actGlobalSetting.setText(QCoreApplication.translate("MainWindow", u"\u5168\u5c40\u8bbe\u7f6e", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"\u6587\u4ef6", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", u"\u7f16\u8f91", None))
        self.menu.setTitle(QCoreApplication.translate("MainWindow", u"\u52a0\u8f7d\u914d\u7f6e", None))
        self.menuAbout.setTitle(QCoreApplication.translate("MainWindow", u"\u5173\u4e8e", None))
        self.menuSettings.setTitle(QCoreApplication.translate("MainWindow", u"\u8bbe\u7f6e", None))
    # retranslateUi

