# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TDDBMonitorImportDialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFrame, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QRadioButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

class Ui_dlgMonitorImport(object):
    def setupUi(self, dlgMonitorImport):
        if not dlgMonitorImport.objectName():
            dlgMonitorImport.setObjectName(u"dlgMonitorImport")
        dlgMonitorImport.resize(1196, 958)
        self.verticalLayout = QVBoxLayout(dlgMonitorImport)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frameContent = QFrame(dlgMonitorImport)
        self.frameContent.setObjectName(u"frameContent")
        self.frameContent.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameContent.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout = QGridLayout(self.frameContent)
        self.gridLayout.setObjectName(u"gridLayout")
        self.editCurrentKeyword = QLineEdit(self.frameContent)
        self.editCurrentKeyword.setObjectName(u"editCurrentKeyword")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.editCurrentKeyword.sizePolicy().hasHeightForWidth())
        self.editCurrentKeyword.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.editCurrentKeyword, 6, 5, 1, 1)

        self.lblSheet = QLabel(self.frameContent)
        self.lblSheet.setObjectName(u"lblSheet")
        self.lblSheet.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.lblSheet, 0, 1, 1, 1)

        self.lblCurrentUnit = QLabel(self.frameContent)
        self.lblCurrentUnit.setObjectName(u"lblCurrentUnit")
        self.lblCurrentUnit.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.lblCurrentUnit, 7, 4, 1, 1)

        self.lblSampleTime = QLabel(self.frameContent)
        self.lblSampleTime.setObjectName(u"lblSampleTime")
        self.lblSampleTime.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.lblSampleTime, 3, 1, 1, 1)

        self.cmbSampleTime = QComboBox(self.frameContent)
        self.cmbSampleTime.setObjectName(u"cmbSampleTime")

        self.gridLayout.addWidget(self.cmbSampleTime, 3, 2, 1, 1)

        self.lblHeaderRow = QLabel(self.frameContent)
        self.lblHeaderRow.setObjectName(u"lblHeaderRow")
        self.lblHeaderRow.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.lblHeaderRow, 1, 1, 1, 1)

        self.gbChannelPreview = QGroupBox(self.frameContent)
        self.gbChannelPreview.setObjectName(u"gbChannelPreview")
        self.verticalLayout_2 = QVBoxLayout(self.gbChannelPreview)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.scrollChannelPreview = QScrollArea(self.gbChannelPreview)
        self.scrollChannelPreview.setObjectName(u"scrollChannelPreview")
        self.scrollChannelPreview.setWidgetResizable(True)
        self.scrollChannelPreviewContent = QWidget()
        self.scrollChannelPreviewContent.setObjectName(u"scrollChannelPreviewContent")
        self.scrollChannelPreviewContent.setGeometry(QRect(0, 0, 799, 527))
        self.scrollChannelPreview.setWidget(self.scrollChannelPreviewContent)

        self.verticalLayout_2.addWidget(self.scrollChannelPreview)

        self.pushButtonApply = QPushButton(self.gbChannelPreview)
        self.pushButtonApply.setObjectName(u"pushButtonApply")

        self.verticalLayout_2.addWidget(self.pushButtonApply)


        self.gridLayout.addWidget(self.gbChannelPreview, 10, 1, 1, 8)

        self.lblAgingTime = QLabel(self.frameContent)
        self.lblAgingTime.setObjectName(u"lblAgingTime")
        self.lblAgingTime.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.lblAgingTime, 3, 4, 1, 1)

        self.scrollFileList = QScrollArea(self.frameContent)
        self.scrollFileList.setObjectName(u"scrollFileList")
        self.scrollFileList.setWidgetResizable(True)
        self.scrollFileListContent = QWidget()
        self.scrollFileListContent.setObjectName(u"scrollFileListContent")
        self.scrollFileListContent.setGeometry(QRect(0, 0, 325, 882))
        self.scrollFileList.setWidget(self.scrollFileListContent)

        self.gridLayout.addWidget(self.scrollFileList, 0, 0, 11, 1)

        self.rdoVoltageFromCol = QRadioButton(self.frameContent)
        self.rdoVoltageFromCol.setObjectName(u"rdoVoltageFromCol")
        self.rdoVoltageFromCol.setChecked(False)

        self.gridLayout.addWidget(self.rdoVoltageFromCol, 6, 1, 1, 1)

        self.lineSep2 = QFrame(self.frameContent)
        self.lineSep2.setObjectName(u"lineSep2")
        self.lineSep2.setFrameShadow(QFrame.Shadow.Plain)
        self.lineSep2.setLineWidth(1)
        self.lineSep2.setMidLineWidth(1)
        self.lineSep2.setFrameShape(QFrame.Shape.HLine)

        self.gridLayout.addWidget(self.lineSep2, 5, 1, 1, 8)

        self.rdoVoltageFixed = QRadioButton(self.frameContent)
        self.rdoVoltageFixed.setObjectName(u"rdoVoltageFixed")

        self.gridLayout.addWidget(self.rdoVoltageFixed, 7, 1, 1, 1)

        self.lineSep3 = QFrame(self.frameContent)
        self.lineSep3.setObjectName(u"lineSep3")
        self.lineSep3.setFrameShadow(QFrame.Shadow.Plain)
        self.lineSep3.setFrameShape(QFrame.Shape.VLine)

        self.gridLayout.addWidget(self.lineSep3, 3, 3, 2, 1)

        self.rdoSampleTimeFromCol = QRadioButton(self.frameContent)
        self.rdoSampleTimeFromCol.setObjectName(u"rdoSampleTimeFromCol")
        self.rdoSampleTimeFromCol.setChecked(True)

        self.gridLayout.addWidget(self.rdoSampleTimeFromCol, 2, 2, 1, 1)

        self.cmbAgingTimeUnit = QComboBox(self.frameContent)
        self.cmbAgingTimeUnit.addItem("")
        self.cmbAgingTimeUnit.addItem("")
        self.cmbAgingTimeUnit.addItem("")
        self.cmbAgingTimeUnit.addItem("")
        self.cmbAgingTimeUnit.addItem("")
        self.cmbAgingTimeUnit.addItem("")
        self.cmbAgingTimeUnit.addItem("")
        self.cmbAgingTimeUnit.setObjectName(u"cmbAgingTimeUnit")

        self.gridLayout.addWidget(self.cmbAgingTimeUnit, 4, 5, 1, 1)

        self.cmbHeaderRow = QComboBox(self.frameContent)
        self.cmbHeaderRow.setObjectName(u"cmbHeaderRow")

        self.gridLayout.addWidget(self.cmbHeaderRow, 1, 2, 1, 7)

        self.cmbAgingTime = QComboBox(self.frameContent)
        self.cmbAgingTime.setObjectName(u"cmbAgingTime")

        self.gridLayout.addWidget(self.cmbAgingTime, 3, 5, 1, 1)

        self.lblCurrentKeyword = QLabel(self.frameContent)
        self.lblCurrentKeyword.setObjectName(u"lblCurrentKeyword")
        self.lblCurrentKeyword.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.lblCurrentKeyword, 6, 4, 1, 1)

        self.cmbSheet = QComboBox(self.frameContent)
        self.cmbSheet.setObjectName(u"cmbSheet")

        self.gridLayout.addWidget(self.cmbSheet, 0, 2, 1, 7)

        self.cmbVoltageCol = QComboBox(self.frameContent)
        self.cmbVoltageCol.setObjectName(u"cmbVoltageCol")

        self.gridLayout.addWidget(self.cmbVoltageCol, 6, 2, 1, 1)

        self.lblTimeSection = QLabel(self.frameContent)
        self.lblTimeSection.setObjectName(u"lblTimeSection")

        self.gridLayout.addWidget(self.lblTimeSection, 2, 1, 1, 1)

        self.lblAgingTimeUnit = QLabel(self.frameContent)
        self.lblAgingTimeUnit.setObjectName(u"lblAgingTimeUnit")
        self.lblAgingTimeUnit.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.lblAgingTimeUnit, 4, 4, 1, 1)

        self.editVoltageFixed = QLineEdit(self.frameContent)
        self.editVoltageFixed.setObjectName(u"editVoltageFixed")
        sizePolicy.setHeightForWidth(self.editVoltageFixed.sizePolicy().hasHeightForWidth())
        self.editVoltageFixed.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.editVoltageFixed, 7, 2, 1, 1)

        self.rdoAgingTimeFromCol = QRadioButton(self.frameContent)
        self.rdoAgingTimeFromCol.setObjectName(u"rdoAgingTimeFromCol")

        self.gridLayout.addWidget(self.rdoAgingTimeFromCol, 2, 4, 1, 1)

        self.cmbTempCol = QComboBox(self.frameContent)
        self.cmbTempCol.setObjectName(u"cmbTempCol")

        self.gridLayout.addWidget(self.cmbTempCol, 6, 8, 1, 1)

        self.cmbCurrentUnit = QComboBox(self.frameContent)
        self.cmbCurrentUnit.addItem("")
        self.cmbCurrentUnit.addItem("")
        self.cmbCurrentUnit.addItem("")
        self.cmbCurrentUnit.addItem("")
        self.cmbCurrentUnit.addItem("")
        self.cmbCurrentUnit.setObjectName(u"cmbCurrentUnit")

        self.gridLayout.addWidget(self.cmbCurrentUnit, 7, 5, 1, 1)

        self.rdoTempCol = QRadioButton(self.frameContent)
        self.rdoTempCol.setObjectName(u"rdoTempCol")

        self.gridLayout.addWidget(self.rdoTempCol, 6, 6, 1, 1)

        self.lblTempUnit = QLabel(self.frameContent)
        self.lblTempUnit.setObjectName(u"lblTempUnit")
        self.lblTempUnit.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.lblTempUnit, 9, 6, 1, 1)

        self.cmbTempUnit = QComboBox(self.frameContent)
        self.cmbTempUnit.addItem("")
        self.cmbTempUnit.addItem("")
        self.cmbTempUnit.addItem("")
        self.cmbTempUnit.setObjectName(u"cmbTempUnit")

        self.gridLayout.addWidget(self.cmbTempUnit, 9, 8, 1, 1)

        self.editTempFixed = QLineEdit(self.frameContent)
        self.editTempFixed.setObjectName(u"editTempFixed")
        sizePolicy.setHeightForWidth(self.editTempFixed.sizePolicy().hasHeightForWidth())
        self.editTempFixed.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.editTempFixed, 7, 8, 1, 1)

        self.rdoTempFixed = QRadioButton(self.frameContent)
        self.rdoTempFixed.setObjectName(u"rdoTempFixed")

        self.gridLayout.addWidget(self.rdoTempFixed, 7, 6, 1, 1)


        self.verticalLayout.addWidget(self.frameContent)

        self.buttonBox = QDialogButtonBox(dlgMonitorImport)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(dlgMonitorImport)

        QMetaObject.connectSlotsByName(dlgMonitorImport)
    # setupUi

    def retranslateUi(self, dlgMonitorImport):
        dlgMonitorImport.setWindowTitle(QCoreApplication.translate("dlgMonitorImport", u"Dialog", None))
        self.lblSheet.setText(QCoreApplication.translate("dlgMonitorImport", u"\u9009\u62e9Sheet\uff1a", None))
        self.lblCurrentUnit.setText(QCoreApplication.translate("dlgMonitorImport", u"\u76d1\u63a7\u7535\u6d41\u5355\u4f4d\uff1a", None))
        self.lblSampleTime.setText(QCoreApplication.translate("dlgMonitorImport", u"\u91c7\u6837\u65f6\u95f4\u5217\uff1a", None))
        self.lblHeaderRow.setText(QCoreApplication.translate("dlgMonitorImport", u"\u9009\u62e9\u9996\u884c\uff1a", None))
        self.gbChannelPreview.setTitle(QCoreApplication.translate("dlgMonitorImport", u"\u76d1\u63a7\u901a\u9053\u9884\u89c8", None))
        self.pushButtonApply.setText(QCoreApplication.translate("dlgMonitorImport", u"\u5e94\u7528", None))
        self.lblAgingTime.setText(QCoreApplication.translate("dlgMonitorImport", u"\u8001\u5316\u65f6\u95f4\u5217\uff1a", None))
        self.rdoVoltageFromCol.setText(QCoreApplication.translate("dlgMonitorImport", u"\u65bd\u52a0\u7535\u538b\u5217", None))
        self.rdoVoltageFixed.setText(QCoreApplication.translate("dlgMonitorImport", u"\u65bd\u52a0\u7535\u538b", None))
        self.rdoSampleTimeFromCol.setText(QCoreApplication.translate("dlgMonitorImport", u"\u91c7\u6837\u65f6\u95f4\u5217", None))
        self.cmbAgingTimeUnit.setItemText(0, QCoreApplication.translate("dlgMonitorImport", u"\u79d2", None))
        self.cmbAgingTimeUnit.setItemText(1, QCoreApplication.translate("dlgMonitorImport", u"\u5206", None))
        self.cmbAgingTimeUnit.setItemText(2, QCoreApplication.translate("dlgMonitorImport", u"\u5c0f\u65f6", None))
        self.cmbAgingTimeUnit.setItemText(3, QCoreApplication.translate("dlgMonitorImport", u"\u5929", None))
        self.cmbAgingTimeUnit.setItemText(4, QCoreApplication.translate("dlgMonitorImport", u"\u5468", None))
        self.cmbAgingTimeUnit.setItemText(5, QCoreApplication.translate("dlgMonitorImport", u"\u6708", None))
        self.cmbAgingTimeUnit.setItemText(6, QCoreApplication.translate("dlgMonitorImport", u"\u5e74", None))

        self.lblCurrentKeyword.setText(QCoreApplication.translate("dlgMonitorImport", u"\u76d1\u63a7\u7535\u6d41\u5173\u952e\u5b57\uff1a", None))
        self.lblTimeSection.setText(QCoreApplication.translate("dlgMonitorImport", u"\u4ee5\u4e0b\u9879\u76ee\u4e8c\u9009\u4e00\uff1a", None))
        self.lblAgingTimeUnit.setText(QCoreApplication.translate("dlgMonitorImport", u"\u8001\u5316\u65f6\u95f4\u5355\u4f4d\uff1a", None))
        self.rdoAgingTimeFromCol.setText(QCoreApplication.translate("dlgMonitorImport", u"\u8001\u5316\u65f6\u95f4\u5217", None))
        self.cmbCurrentUnit.setItemText(0, QCoreApplication.translate("dlgMonitorImport", u"nA", None))
        self.cmbCurrentUnit.setItemText(1, QCoreApplication.translate("dlgMonitorImport", u"pA", None))
        self.cmbCurrentUnit.setItemText(2, QCoreApplication.translate("dlgMonitorImport", u"uA", None))
        self.cmbCurrentUnit.setItemText(3, QCoreApplication.translate("dlgMonitorImport", u"mA", None))
        self.cmbCurrentUnit.setItemText(4, QCoreApplication.translate("dlgMonitorImport", u"A", None))

        self.rdoTempCol.setText(QCoreApplication.translate("dlgMonitorImport", u"\u76d1\u63a7\u6e29\u5ea6\u5217\uff1a", None))
        self.lblTempUnit.setText(QCoreApplication.translate("dlgMonitorImport", u"\u76d1\u63a7\u6e29\u5ea6\u5355\u4f4d\uff1a", None))
        self.cmbTempUnit.setItemText(0, QCoreApplication.translate("dlgMonitorImport", u"\u2103", None))
        self.cmbTempUnit.setItemText(1, QCoreApplication.translate("dlgMonitorImport", u"K", None))
        self.cmbTempUnit.setItemText(2, QCoreApplication.translate("dlgMonitorImport", u"F", None))

        self.rdoTempFixed.setText(QCoreApplication.translate("dlgMonitorImport", u"\u8003\u6838\u6e29\u5ea6", None))
    # retranslateUi

