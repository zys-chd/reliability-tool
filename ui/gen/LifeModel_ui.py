# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'LifeModel.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QSizePolicy, QTabWidget, QVBoxLayout,
    QWidget)

class Ui_LifeModelPage(object):
    def setupUi(self, LifeModelPage):
        if not LifeModelPage.objectName():
            LifeModelPage.setObjectName(u"LifeModelPage")
        LifeModelPage.resize(1319, 865)
        self.verticalLayout = QVBoxLayout(LifeModelPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(LifeModelPage)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.South)
        self.tabWidget.setTabShape(QTabWidget.TabShape.Rounded)
        self.tabWidget.setElideMode(Qt.TextElideMode.ElideNone)
        self.tabWidget.setTabsClosable(False)
        self.tabWidget.setMovable(True)
        self.tabWidget.setTabBarAutoHide(False)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.tabWidget.addTab(self.tab_4, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.tabWidget.addTab(self.tab_5, "")
        self.tab_6 = QWidget()
        self.tab_6.setObjectName(u"tab_6")
        self.tabWidget.addTab(self.tab_6, "")

        self.verticalLayout.addWidget(self.tabWidget)


        self.retranslateUi(LifeModelPage)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(LifeModelPage)
    # setupUi

    def retranslateUi(self, LifeModelPage):
        LifeModelPage.setWindowTitle(QCoreApplication.translate("LifeModelPage", u"LifeModelPage", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("LifeModelPage", u"\u57fa\u677f\u5bff\u547d", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("LifeModelPage", u"HTRB\u5bff\u547d", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("LifeModelPage", u"\u6e7f\u6c14\u5bff\u547d", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("LifeModelPage", u"PC\u5bff\u547d", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("LifeModelPage", u"\u9ad8\u963b", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), QCoreApplication.translate("LifeModelPage", u"\u7ed3\u5408\u529b", None))
    # retranslateUi

