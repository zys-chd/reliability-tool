# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TDDBSetting.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(922, 636)
        self.vlMain = QVBoxLayout(Form)
        self.vlMain.setObjectName(u"vlMain")
        self.scrollSetting = QScrollArea(Form)
        self.scrollSetting.setObjectName(u"scrollSetting")
        self.scrollSetting.setWidgetResizable(True)
        self.scrollSettingContent = QWidget()
        self.scrollSettingContent.setObjectName(u"scrollSettingContent")
        self.scrollSettingContent.setGeometry(QRect(0, 0, 902, 616))
        self.vlSettingContent = QVBoxLayout(self.scrollSettingContent)
        self.vlSettingContent.setObjectName(u"vlSettingContent")
        self.gbWeibull = QGroupBox(self.scrollSettingContent)
        self.gbWeibull.setObjectName(u"gbWeibull")
        self.vlWeibull = QVBoxLayout(self.gbWeibull)
        self.vlWeibull.setObjectName(u"vlWeibull")
        self.frameFile = QFrame(self.gbWeibull)
        self.frameFile.setObjectName(u"frameFile")
        self.frameFile.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameFile.setFrameShadow(QFrame.Shadow.Raised)
        self.hlFile = QHBoxLayout(self.frameFile)
        self.hlFile.setObjectName(u"hlFile")
        self.lblFilePath = QLabel(self.frameFile)
        self.lblFilePath.setObjectName(u"lblFilePath")

        self.hlFile.addWidget(self.lblFilePath)

        self.horizontalSpacer_File = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlFile.addItem(self.horizontalSpacer_File)

        self.editFilePath = QLineEdit(self.frameFile)
        self.editFilePath.setObjectName(u"editFilePath")

        self.hlFile.addWidget(self.editFilePath)

        self.btnBrowseFile = QPushButton(self.frameFile)
        self.btnBrowseFile.setObjectName(u"btnBrowseFile")

        self.hlFile.addWidget(self.btnBrowseFile)


        self.vlWeibull.addWidget(self.frameFile)

        self.frameSheet = QFrame(self.gbWeibull)
        self.frameSheet.setObjectName(u"frameSheet")
        self.frameSheet.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameSheet.setFrameShadow(QFrame.Shadow.Raised)
        self.hlSheet = QHBoxLayout(self.frameSheet)
        self.hlSheet.setObjectName(u"hlSheet")
        self.lblSheet = QLabel(self.frameSheet)
        self.lblSheet.setObjectName(u"lblSheet")

        self.hlSheet.addWidget(self.lblSheet)

        self.horizontalSpacer_Sheet = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlSheet.addItem(self.horizontalSpacer_Sheet)

        self.cmbSheetName = QComboBox(self.frameSheet)
        self.cmbSheetName.setObjectName(u"cmbSheetName")

        self.hlSheet.addWidget(self.cmbSheetName)


        self.vlWeibull.addWidget(self.frameSheet)


        self.vlSettingContent.addWidget(self.gbWeibull)

        self.gbLifetime = QGroupBox(self.scrollSettingContent)
        self.gbLifetime.setObjectName(u"gbLifetime")
        self.vlLifetime = QVBoxLayout(self.gbLifetime)
        self.vlLifetime.setObjectName(u"vlLifetime")
        self.frameVoltage = QFrame(self.gbLifetime)
        self.frameVoltage.setObjectName(u"frameVoltage")
        self.frameVoltage.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameVoltage.setFrameShadow(QFrame.Shadow.Raised)
        self.hlVoltage = QHBoxLayout(self.frameVoltage)
        self.hlVoltage.setObjectName(u"hlVoltage")
        self.lblWorkVoltage = QLabel(self.frameVoltage)
        self.lblWorkVoltage.setObjectName(u"lblWorkVoltage")

        self.hlVoltage.addWidget(self.lblWorkVoltage)

        self.horizontalSpacer_Voltage = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlVoltage.addItem(self.horizontalSpacer_Voltage)

        self.spnWorkVoltage = QDoubleSpinBox(self.frameVoltage)
        self.spnWorkVoltage.setObjectName(u"spnWorkVoltage")
        self.spnWorkVoltage.setDecimals(1)
        self.spnWorkVoltage.setMinimum(-5000.000000000000000)
        self.spnWorkVoltage.setMaximum(5000.000000000000000)
        self.spnWorkVoltage.setValue(18.000000000000000)

        self.hlVoltage.addWidget(self.spnWorkVoltage)


        self.vlLifetime.addWidget(self.frameVoltage)

        self.frameTemp = QFrame(self.gbLifetime)
        self.frameTemp.setObjectName(u"frameTemp")
        self.frameTemp.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameTemp.setFrameShadow(QFrame.Shadow.Raised)
        self.hlTemp = QHBoxLayout(self.frameTemp)
        self.hlTemp.setObjectName(u"hlTemp")
        self.lblWorkTemp = QLabel(self.frameTemp)
        self.lblWorkTemp.setObjectName(u"lblWorkTemp")

        self.hlTemp.addWidget(self.lblWorkTemp)

        self.horizontalSpacer_Temp = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlTemp.addItem(self.horizontalSpacer_Temp)

        self.spnWorkTemp = QDoubleSpinBox(self.frameTemp)
        self.spnWorkTemp.setObjectName(u"spnWorkTemp")
        self.spnWorkTemp.setDecimals(1)
        self.spnWorkTemp.setMinimum(-5000.000000000000000)
        self.spnWorkTemp.setMaximum(5000.000000000000000)
        self.spnWorkTemp.setValue(150.000000000000000)

        self.hlTemp.addWidget(self.spnWorkTemp)


        self.vlLifetime.addWidget(self.frameTemp)

        self.frameOxide = QFrame(self.gbLifetime)
        self.frameOxide.setObjectName(u"frameOxide")
        self.frameOxide.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameOxide.setFrameShadow(QFrame.Shadow.Raised)
        self.hlOxide = QHBoxLayout(self.frameOxide)
        self.hlOxide.setObjectName(u"hlOxide")
        self.lblOxideThickness = QLabel(self.frameOxide)
        self.lblOxideThickness.setObjectName(u"lblOxideThickness")

        self.hlOxide.addWidget(self.lblOxideThickness)

        self.horizontalSpacer_Oxide = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlOxide.addItem(self.horizontalSpacer_Oxide)

        self.spnOxideThickness = QDoubleSpinBox(self.frameOxide)
        self.spnOxideThickness.setObjectName(u"spnOxideThickness")
        self.spnOxideThickness.setDecimals(1)
        self.spnOxideThickness.setMinimum(-5000.000000000000000)
        self.spnOxideThickness.setMaximum(5000.000000000000000)
        self.spnOxideThickness.setValue(52.000000000000000)

        self.hlOxide.addWidget(self.spnOxideThickness)


        self.vlLifetime.addWidget(self.frameOxide)

        self.frameModel = QFrame(self.gbLifetime)
        self.frameModel.setObjectName(u"frameModel")
        self.frameModel.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameModel.setFrameShadow(QFrame.Shadow.Raised)
        self.hlModel = QHBoxLayout(self.frameModel)
        self.hlModel.setObjectName(u"hlModel")
        self.lblTDDBModel = QLabel(self.frameModel)
        self.lblTDDBModel.setObjectName(u"lblTDDBModel")

        self.hlModel.addWidget(self.lblTDDBModel)

        self.horizontalSpacer_Model = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlModel.addItem(self.horizontalSpacer_Model)

        self.cmbTDDBModel = QComboBox(self.frameModel)
        self.cmbTDDBModel.addItem("")
        self.cmbTDDBModel.addItem("")
        self.cmbTDDBModel.addItem("")
        self.cmbTDDBModel.setObjectName(u"cmbTDDBModel")

        self.hlModel.addWidget(self.cmbTDDBModel)


        self.vlLifetime.addWidget(self.frameModel)

        self.framePickMethod = QFrame(self.gbLifetime)
        self.framePickMethod.setObjectName(u"framePickMethod")
        self.framePickMethod.setFrameShape(QFrame.Shape.StyledPanel)
        self.framePickMethod.setFrameShadow(QFrame.Shadow.Raised)
        self.hlPickMethod = QHBoxLayout(self.framePickMethod)
        self.hlPickMethod.setObjectName(u"hlPickMethod")
        self.lblPickMethod = QLabel(self.framePickMethod)
        self.lblPickMethod.setObjectName(u"lblPickMethod")

        self.hlPickMethod.addWidget(self.lblPickMethod)

        self.horizontalSpacer_PickMethod = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlPickMethod.addItem(self.horizontalSpacer_PickMethod)

        self.cmbPickMethod = QComboBox(self.framePickMethod)
        self.cmbPickMethod.addItem("")
        self.cmbPickMethod.addItem("")
        self.cmbPickMethod.setObjectName(u"cmbPickMethod")

        self.hlPickMethod.addWidget(self.cmbPickMethod)


        self.vlLifetime.addWidget(self.framePickMethod)

        self.frameSaveDir = QFrame(self.gbLifetime)
        self.frameSaveDir.setObjectName(u"frameSaveDir")
        self.frameSaveDir.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameSaveDir.setFrameShadow(QFrame.Shadow.Raised)
        self.hlSaveDir = QHBoxLayout(self.frameSaveDir)
        self.hlSaveDir.setObjectName(u"hlSaveDir")
        self.lblSaveDir = QLabel(self.frameSaveDir)
        self.lblSaveDir.setObjectName(u"lblSaveDir")

        self.hlSaveDir.addWidget(self.lblSaveDir)

        self.horizontalSpacer_SaveDir = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlSaveDir.addItem(self.horizontalSpacer_SaveDir)

        self.editSaveDir = QLineEdit(self.frameSaveDir)
        self.editSaveDir.setObjectName(u"editSaveDir")

        self.hlSaveDir.addWidget(self.editSaveDir)

        self.btnBrowseSaveDir = QPushButton(self.frameSaveDir)
        self.btnBrowseSaveDir.setObjectName(u"btnBrowseSaveDir")

        self.hlSaveDir.addWidget(self.btnBrowseSaveDir)


        self.vlLifetime.addWidget(self.frameSaveDir)


        self.vlSettingContent.addWidget(self.gbLifetime)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlSettingContent.addItem(self.verticalSpacer)

        self.scrollSetting.setWidget(self.scrollSettingContent)

        self.vlMain.addWidget(self.scrollSetting)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.gbWeibull.setTitle(QCoreApplication.translate("Form", u"weibull\u5206\u5e03", None))
        self.lblFilePath.setText(QCoreApplication.translate("Form", u"\u6587\u4ef6\u5730\u5740\uff1a", None))
        self.btnBrowseFile.setText(QCoreApplication.translate("Form", u"\u9009\u62e9", None))
        self.lblSheet.setText(QCoreApplication.translate("Form", u"sheet\u540d\u79f0\uff1a", None))
        self.gbLifetime.setTitle(QCoreApplication.translate("Form", u"\u5bff\u547d\u8ba1\u7b97", None))
        self.lblWorkVoltage.setText(QCoreApplication.translate("Form", u"\u5de5\u4f5c\u7535\u538b/V:", None))
        self.lblWorkTemp.setText(QCoreApplication.translate("Form", u"\u5de5\u4f5c\u6e29\u5ea6/\u2103:", None))
        self.lblOxideThickness.setText(QCoreApplication.translate("Form", u"\u6805\u6c27\u539a\u5ea6/nm\uff1a", None))
        self.lblTDDBModel.setText(QCoreApplication.translate("Form", u"TDDB\u6a21\u578b\uff1a", None))
        self.cmbTDDBModel.setItemText(0, QCoreApplication.translate("Form", u"E\u6a21\u578b", None))
        self.cmbTDDBModel.setItemText(1, QCoreApplication.translate("Form", u"1/E\u6a21\u578b", None))
        self.cmbTDDBModel.setItemText(2, QCoreApplication.translate("Form", u"V\u6a21\u578b", None))

        self.lblPickMethod.setText(QCoreApplication.translate("Form", u"\u53d6\u70b9\u65b9\u5f0f\uff1a", None))
        self.cmbPickMethod.setItemText(0, QCoreApplication.translate("Form", u"weibull\u66f2\u7ebf\u53d6\u70b9", None))
        self.cmbPickMethod.setItemText(1, QCoreApplication.translate("Form", u"\u539f\u59cb\u6570\u636e\u5e73\u6ed1\u53d6\u70b9", None))

        self.lblSaveDir.setText(QCoreApplication.translate("Form", u"\u4e34\u65f6\u4fdd\u5b58\u76ee\u5f55\uff1a", None))
        self.editSaveDir.setText(QCoreApplication.translate("Form", u"%PROGRAME_DIR%/images", None))
        self.btnBrowseSaveDir.setText(QCoreApplication.translate("Form", u"\u9009\u62e9", None))
    # retranslateUi

