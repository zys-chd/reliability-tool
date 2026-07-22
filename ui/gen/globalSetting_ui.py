# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'globalSetting.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QScrollArea, QSizePolicy,
    QSpacerItem, QSpinBox, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(944, 677)
        self.vlMain = QVBoxLayout(Form)
        self.vlMain.setObjectName(u"vlMain")
        self.scrollGlobal = QScrollArea(Form)
        self.scrollGlobal.setObjectName(u"scrollGlobal")
        self.scrollGlobal.setWidgetResizable(True)
        self.scrollGlobalContent = QWidget()
        self.scrollGlobalContent.setObjectName(u"scrollGlobalContent")
        self.scrollGlobalContent.setGeometry(QRect(0, 0, 924, 657))
        self.vlContent = QVBoxLayout(self.scrollGlobalContent)
        self.vlContent.setObjectName(u"vlContent")
        self.gbWindow = QGroupBox(self.scrollGlobalContent)
        self.gbWindow.setObjectName(u"gbWindow")
        self.vlWindow = QVBoxLayout(self.gbWindow)
        self.vlWindow.setObjectName(u"vlWindow")
        self.frameSize = QFrame(self.gbWindow)
        self.frameSize.setObjectName(u"frameSize")
        self.frameSize.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameSize.setFrameShadow(QFrame.Shadow.Raised)
        self.hlSize = QHBoxLayout(self.frameSize)
        self.hlSize.setObjectName(u"hlSize")
        self.lblWinSize = QLabel(self.frameSize)
        self.lblWinSize.setObjectName(u"lblWinSize")

        self.hlSize.addWidget(self.lblWinSize)

        self.spSize = QSpacerItem(561, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlSize.addItem(self.spSize)

        self.lblHeight = QLabel(self.frameSize)
        self.lblHeight.setObjectName(u"lblHeight")

        self.hlSize.addWidget(self.lblHeight)

        self.spnWinHeight = QSpinBox(self.frameSize)
        self.spnWinHeight.setObjectName(u"spnWinHeight")
        self.spnWinHeight.setMinimumSize(QSize(120, 0))
        self.spnWinHeight.setMinimum(600)
        self.spnWinHeight.setMaximum(10000)
        self.spnWinHeight.setValue(692)

        self.hlSize.addWidget(self.spnWinHeight)

        self.lblWidth = QLabel(self.frameSize)
        self.lblWidth.setObjectName(u"lblWidth")

        self.hlSize.addWidget(self.lblWidth)

        self.spnWinWidth = QSpinBox(self.frameSize)
        self.spnWinWidth.setObjectName(u"spnWinWidth")
        self.spnWinWidth.setMinimumSize(QSize(120, 0))
        self.spnWinWidth.setMinimum(400)
        self.spnWinWidth.setMaximum(10000)
        self.spnWinWidth.setValue(910)

        self.hlSize.addWidget(self.spnWinWidth)


        self.vlWindow.addWidget(self.frameSize)

        self.framePosition = QFrame(self.gbWindow)
        self.framePosition.setObjectName(u"framePosition")
        self.framePosition.setFrameShape(QFrame.Shape.StyledPanel)
        self.framePosition.setFrameShadow(QFrame.Shadow.Raised)
        self.hlPosition = QHBoxLayout(self.framePosition)
        self.hlPosition.setObjectName(u"hlPosition")
        self.lblWinPos = QLabel(self.framePosition)
        self.lblWinPos.setObjectName(u"lblWinPos")

        self.hlPosition.addWidget(self.lblWinPos)

        self.spPosition = QSpacerItem(546, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlPosition.addItem(self.spPosition)

        self.cmbWinPosition = QComboBox(self.framePosition)
        self.cmbWinPosition.addItem("")
        self.cmbWinPosition.addItem("")
        self.cmbWinPosition.addItem("")
        self.cmbWinPosition.addItem("")
        self.cmbWinPosition.addItem("")
        self.cmbWinPosition.addItem("")
        self.cmbWinPosition.addItem("")
        self.cmbWinPosition.addItem("")
        self.cmbWinPosition.addItem("")
        self.cmbWinPosition.addItem("")
        self.cmbWinPosition.setObjectName(u"cmbWinPosition")
        self.cmbWinPosition.setMinimumSize(QSize(240, 0))

        self.hlPosition.addWidget(self.cmbWinPosition)


        self.vlWindow.addWidget(self.framePosition)

        self.frameFontSize = QFrame(self.gbWindow)
        self.frameFontSize.setObjectName(u"frameFontSize")
        self.frameFontSize.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameFontSize.setFrameShadow(QFrame.Shadow.Raised)
        self.hlFontSize = QHBoxLayout(self.frameFontSize)
        self.hlFontSize.setObjectName(u"hlFontSize")
        self.lblFontSize = QLabel(self.frameFontSize)
        self.lblFontSize.setObjectName(u"lblFontSize")

        self.hlFontSize.addWidget(self.lblFontSize)

        self.spFontSize = QSpacerItem(546, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlFontSize.addItem(self.spFontSize)

        self.spnFontSize = QSpinBox(self.frameFontSize)
        self.spnFontSize.setObjectName(u"spnFontSize")
        self.spnFontSize.setMinimumSize(QSize(80, 0))
        self.spnFontSize.setMinimum(2)
        self.spnFontSize.setMaximum(100)
        self.spnFontSize.setValue(12)

        self.hlFontSize.addWidget(self.spnFontSize)


        self.vlWindow.addWidget(self.frameFontSize)

        self.frameCnFont = QFrame(self.gbWindow)
        self.frameCnFont.setObjectName(u"frameCnFont")
        self.frameCnFont.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameCnFont.setFrameShadow(QFrame.Shadow.Raised)
        self.hlCnFont = QHBoxLayout(self.frameCnFont)
        self.hlCnFont.setObjectName(u"hlCnFont")
        self.lblCnFont = QLabel(self.frameCnFont)
        self.lblCnFont.setObjectName(u"lblCnFont")

        self.hlCnFont.addWidget(self.lblCnFont)

        self.spCnFont = QSpacerItem(546, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlCnFont.addItem(self.spCnFont)

        self.cmbCnFont = QComboBox(self.frameCnFont)
        self.cmbCnFont.setObjectName(u"cmbCnFont")
        self.cmbCnFont.setMinimumSize(QSize(240, 0))

        self.hlCnFont.addWidget(self.cmbCnFont)


        self.vlWindow.addWidget(self.frameCnFont)

        self.frameEnFont = QFrame(self.gbWindow)
        self.frameEnFont.setObjectName(u"frameEnFont")
        self.frameEnFont.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameEnFont.setFrameShadow(QFrame.Shadow.Raised)
        self.hlEnFont = QHBoxLayout(self.frameEnFont)
        self.hlEnFont.setObjectName(u"hlEnFont")
        self.lblEnFont = QLabel(self.frameEnFont)
        self.lblEnFont.setObjectName(u"lblEnFont")

        self.hlEnFont.addWidget(self.lblEnFont)

        self.spEnFont = QSpacerItem(546, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlEnFont.addItem(self.spEnFont)

        self.cmbEnFont = QComboBox(self.frameEnFont)
        self.cmbEnFont.setObjectName(u"cmbEnFont")
        self.cmbEnFont.setMinimumSize(QSize(240, 0))

        self.hlEnFont.addWidget(self.cmbEnFont)


        self.vlWindow.addWidget(self.frameEnFont)


        self.vlContent.addWidget(self.gbWindow)

        self.gbExit = QGroupBox(self.scrollGlobalContent)
        self.gbExit.setObjectName(u"gbExit")
        self.vlExit = QVBoxLayout(self.gbExit)
        self.vlExit.setObjectName(u"vlExit")
        self.frameClean = QFrame(self.gbExit)
        self.frameClean.setObjectName(u"frameClean")
        self.frameClean.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameClean.setFrameShadow(QFrame.Shadow.Raised)
        self.hlClean = QHBoxLayout(self.frameClean)
        self.hlClean.setObjectName(u"hlClean")
        self.lblClean = QLabel(self.frameClean)
        self.lblClean.setObjectName(u"lblClean")

        self.hlClean.addWidget(self.lblClean)

        self.spClean = QSpacerItem(546, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlClean.addItem(self.spClean)

        self.cmbCleanOnExit = QComboBox(self.frameClean)
        self.cmbCleanOnExit.addItem("")
        self.cmbCleanOnExit.addItem("")
        self.cmbCleanOnExit.setObjectName(u"cmbCleanOnExit")
        self.cmbCleanOnExit.setMinimumSize(QSize(50, 0))

        self.hlClean.addWidget(self.cmbCleanOnExit)


        self.vlExit.addWidget(self.frameClean)


        self.vlContent.addWidget(self.gbExit)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlContent.addItem(self.verticalSpacer)

        self.scrollGlobal.setWidget(self.scrollGlobalContent)

        self.vlMain.addWidget(self.scrollGlobal)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.gbWindow.setTitle(QCoreApplication.translate("Form", u"\u7a97\u53e3\u8bbe\u7f6e", None))
        self.lblWinSize.setText(QCoreApplication.translate("Form", u"\u7a97\u53e3\u5c3a\u5bf8", None))
        self.lblHeight.setText(QCoreApplication.translate("Form", u"\u9ad8\uff1a", None))
        self.spnWinHeight.setSuffix(QCoreApplication.translate("Form", u" px", None))
        self.lblWidth.setText(QCoreApplication.translate("Form", u"\u5bbd\uff1a", None))
        self.spnWinWidth.setSuffix(QCoreApplication.translate("Form", u" px", None))
        self.lblWinPos.setText(QCoreApplication.translate("Form", u"\u7a97\u53e3\u542f\u52a8\u4f4d\u7f6e", None))
        self.cmbWinPosition.setItemText(0, QCoreApplication.translate("Form", u"\u8bb0\u5fc6\u4e0a\u6b21\u5173\u95ed\u65f6\u4f4d\u7f6e", None))
        self.cmbWinPosition.setItemText(1, QCoreApplication.translate("Form", u"\u4e2d\u5fc3", None))
        self.cmbWinPosition.setItemText(2, QCoreApplication.translate("Form", u"\u5de6\u4e0a", None))
        self.cmbWinPosition.setItemText(3, QCoreApplication.translate("Form", u"\u53f3\u4e0a", None))
        self.cmbWinPosition.setItemText(4, QCoreApplication.translate("Form", u"\u5de6\u4e0b", None))
        self.cmbWinPosition.setItemText(5, QCoreApplication.translate("Form", u"\u53f3\u4e0b", None))
        self.cmbWinPosition.setItemText(6, QCoreApplication.translate("Form", u"\u4e0a\u65b9", None))
        self.cmbWinPosition.setItemText(7, QCoreApplication.translate("Form", u"\u4e0b\u65b9", None))
        self.cmbWinPosition.setItemText(8, QCoreApplication.translate("Form", u"\u5de6\u65b9", None))
        self.cmbWinPosition.setItemText(9, QCoreApplication.translate("Form", u"\u53f3\u65b9", None))

        self.lblFontSize.setText(QCoreApplication.translate("Form", u"\u9ed8\u8ba4\u5b57\u4f53\u5927\u5c0f", None))
        self.spnFontSize.setSuffix(QCoreApplication.translate("Form", u" pt", None))
        self.lblCnFont.setText(QCoreApplication.translate("Form", u"\u9ed8\u8ba4\u4e2d\u6587\u5b57\u4f53", None))
        self.lblEnFont.setText(QCoreApplication.translate("Form", u"\u9ed8\u8ba4\u897f\u6587\u5b57\u4f53", None))
        self.gbExit.setTitle(QCoreApplication.translate("Form", u"\u9000\u51fa\u8bbe\u7f6e", None))
        self.lblClean.setText(QCoreApplication.translate("Form", u"\u9000\u51fa\u524d\u6e05\u7406\u6587\u4ef6", None))
        self.cmbCleanOnExit.setItemText(0, QCoreApplication.translate("Form", u"\u662f", None))
        self.cmbCleanOnExit.setItemText(1, QCoreApplication.translate("Form", u"\u5426", None))

    # retranslateUi

