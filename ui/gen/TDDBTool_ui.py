# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TDDBTool.ui'
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
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QRadioButton,
    QScrollArea, QSizePolicy, QSpacerItem, QSplitter,
    QTabWidget, QTableView, QTableWidget, QTableWidgetItem,
    QToolButton, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1638, 1133)
        self.mainLayout = QVBoxLayout(Form)
        self.mainLayout.setObjectName(u"mainLayout")
        self.twMain = QTabWidget(Form)
        self.twMain.setObjectName(u"twMain")
        self.twMain.setTabPosition(QTabWidget.TabPosition.West)
        self.tbMonitorImport = QWidget()
        self.tbMonitorImport.setObjectName(u"tbMonitorImport")
        self.verticalLayout_2 = QVBoxLayout(self.tbMonitorImport)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.splMonitor = QSplitter(self.tbMonitorImport)
        self.splMonitor.setObjectName(u"splMonitor")
        self.splMonitor.setOrientation(Qt.Orientation.Horizontal)
        self.frameMonitorLeft = QFrame(self.splMonitor)
        self.frameMonitorLeft.setObjectName(u"frameMonitorLeft")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frameMonitorLeft.sizePolicy().hasHeightForWidth())
        self.frameMonitorLeft.setSizePolicy(sizePolicy)
        self.frameMonitorLeft.setMinimumSize(QSize(900, 0))
        self.frameMonitorLeft.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameMonitorLeft.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frameMonitorLeft)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gbFileHandling = QGroupBox(self.frameMonitorLeft)
        self.gbFileHandling.setObjectName(u"gbFileHandling")
        self.gridLayout = QGridLayout(self.gbFileHandling)
        self.gridLayout.setObjectName(u"gridLayout")
        self.btnRemoveAll = QPushButton(self.gbFileHandling)
        self.btnRemoveAll.setObjectName(u"btnRemoveAll")

        self.gridLayout.addWidget(self.btnRemoveAll, 2, 2, 1, 1)

        self.btnRemoveSelected = QPushButton(self.gbFileHandling)
        self.btnRemoveSelected.setObjectName(u"btnRemoveSelected")

        self.gridLayout.addWidget(self.btnRemoveSelected, 1, 2, 1, 1)

        self.btnAddFile = QPushButton(self.gbFileHandling)
        self.btnAddFile.setObjectName(u"btnAddFile")

        self.gridLayout.addWidget(self.btnAddFile, 0, 2, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.verticalSpacer_4, 3, 2, 1, 1)

        self.scrollFileList = QScrollArea(self.gbFileHandling)
        self.scrollFileList.setObjectName(u"scrollFileList")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.scrollFileList.sizePolicy().hasHeightForWidth())
        self.scrollFileList.setSizePolicy(sizePolicy1)
        self.scrollFileList.setWidgetResizable(True)
        self.scrollFileListContent = QWidget()
        self.scrollFileListContent.setObjectName(u"scrollFileListContent")
        self.scrollFileListContent.setGeometry(QRect(0, 0, 768, 106))
        self.scrollFileList.setWidget(self.scrollFileListContent)

        self.gridLayout.addWidget(self.scrollFileList, 0, 0, 5, 2)


        self.verticalLayout.addWidget(self.gbFileHandling)

        self.gbPreviewConfig = QGroupBox(self.frameMonitorLeft)
        self.gbPreviewConfig.setObjectName(u"gbPreviewConfig")
        self.gridLayout_2 = QGridLayout(self.gbPreviewConfig)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.lblRateLimit = QLabel(self.gbPreviewConfig)
        self.lblRateLimit.setObjectName(u"lblRateLimit")
        self.lblRateLimit.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.lblRateLimit, 2, 2, 1, 1)

        self.btnExportData = QPushButton(self.gbPreviewConfig)
        self.btnExportData.setObjectName(u"btnExportData")

        self.gridLayout_2.addWidget(self.btnExportData, 5, 0, 1, 2)

        self.chkFailCurrentDrop = QCheckBox(self.gbPreviewConfig)
        self.chkFailCurrentDrop.setObjectName(u"chkFailCurrentDrop")
        self.chkFailCurrentDrop.setChecked(True)

        self.gridLayout_2.addWidget(self.chkFailCurrentDrop, 0, 1, 1, 1)

        self.cmbPreviewFile = QComboBox(self.gbPreviewConfig)
        self.cmbPreviewFile.setObjectName(u"cmbPreviewFile")

        self.gridLayout_2.addWidget(self.cmbPreviewFile, 3, 1, 1, 1)

        self.chklogY = QCheckBox(self.gbPreviewConfig)
        self.chklogY.setObjectName(u"chklogY")
        self.chklogY.setChecked(False)

        self.gridLayout_2.addWidget(self.chklogY, 1, 4, 1, 1)

        self.chkFailCurrentLimit = QCheckBox(self.gbPreviewConfig)
        self.chkFailCurrentLimit.setObjectName(u"chkFailCurrentLimit")
        self.chkFailCurrentLimit.setChecked(True)

        self.gridLayout_2.addWidget(self.chkFailCurrentLimit, 1, 1, 1, 1)

        self.lblCurrentLimit = QLabel(self.gbPreviewConfig)
        self.lblCurrentLimit.setObjectName(u"lblCurrentLimit")
        self.lblCurrentLimit.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.lblCurrentLimit, 2, 0, 1, 1)

        self.chkFailHalfTime = QCheckBox(self.gbPreviewConfig)
        self.chkFailHalfTime.setObjectName(u"chkFailHalfTime")
        self.chkFailHalfTime.setChecked(True)

        self.gridLayout_2.addWidget(self.chkFailHalfTime, 1, 2, 1, 1)

        self.btnToWeibullFit = QPushButton(self.gbPreviewConfig)
        self.btnToWeibullFit.setObjectName(u"btnToWeibullFit")

        self.gridLayout_2.addWidget(self.btnToWeibullFit, 5, 2, 1, 3)

        self.lblFailLogic = QLabel(self.gbPreviewConfig)
        self.lblFailLogic.setObjectName(u"lblFailLogic")
        self.lblFailLogic.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.lblFailLogic, 0, 0, 1, 1)

        self.spnCurrentLimit = QDoubleSpinBox(self.gbPreviewConfig)
        self.spnCurrentLimit.setObjectName(u"spnCurrentLimit")
        self.spnCurrentLimit.setDecimals(4)
        self.spnCurrentLimit.setValue(1.000000000000000)

        self.gridLayout_2.addWidget(self.spnCurrentLimit, 2, 1, 1, 1)

        self.spnRateLimit = QDoubleSpinBox(self.gbPreviewConfig)
        self.spnRateLimit.setObjectName(u"spnRateLimit")
        self.spnRateLimit.setValue(10.000000000000000)

        self.gridLayout_2.addWidget(self.spnRateLimit, 2, 4, 1, 1)

        self.chkFailRateExceed = QCheckBox(self.gbPreviewConfig)
        self.chkFailRateExceed.setObjectName(u"chkFailRateExceed")
        self.chkFailRateExceed.setChecked(True)

        self.gridLayout_2.addWidget(self.chkFailRateExceed, 0, 2, 1, 1)

        self.chklogX = QCheckBox(self.gbPreviewConfig)
        self.chklogX.setObjectName(u"chklogX")
        self.chklogX.setChecked(False)

        self.gridLayout_2.addWidget(self.chklogX, 0, 4, 1, 1)

        self.lblPreviewFile = QLabel(self.gbPreviewConfig)
        self.lblPreviewFile.setObjectName(u"lblPreviewFile")
        self.lblPreviewFile.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.lblPreviewFile, 3, 0, 1, 1)

        self.scrollDataTable = QScrollArea(self.gbPreviewConfig)
        self.scrollDataTable.setObjectName(u"scrollDataTable")
        self.scrollDataTable.setWidgetResizable(True)
        self.scrollDataTableContent = QWidget()
        self.scrollDataTableContent.setObjectName(u"scrollDataTableContent")
        self.scrollDataTableContent.setGeometry(QRect(0, 0, 854, 696))
        self.verticalLayout_4 = QVBoxLayout(self.scrollDataTableContent)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.tblMonitorData = QTableWidget(self.scrollDataTableContent)
        self.tblMonitorData.setObjectName(u"tblMonitorData")

        self.verticalLayout_4.addWidget(self.tblMonitorData)

        self.scrollDataTable.setWidget(self.scrollDataTableContent)

        self.gridLayout_2.addWidget(self.scrollDataTable, 4, 0, 1, 5)

        self.line = QFrame(self.gbPreviewConfig)
        self.line.setObjectName(u"line")
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        self.line.setFrameShape(QFrame.Shape.VLine)

        self.gridLayout_2.addWidget(self.line, 0, 3, 2, 1)


        self.verticalLayout.addWidget(self.gbPreviewConfig)

        self.splMonitor.addWidget(self.frameMonitorLeft)
        self.gbMonitorPlot = QGroupBox(self.splMonitor)
        self.gbMonitorPlot.setObjectName(u"gbMonitorPlot")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(1)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.gbMonitorPlot.sizePolicy().hasHeightForWidth())
        self.gbMonitorPlot.setSizePolicy(sizePolicy2)
        self.verticalLayout_3 = QVBoxLayout(self.gbMonitorPlot)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.wvMonitorPlot = QWebEngineView(self.gbMonitorPlot)
        self.wvMonitorPlot.setObjectName(u"wvMonitorPlot")
        self.wvMonitorPlot.setUrl(QUrl(u"about:blank"))

        self.verticalLayout_3.addWidget(self.wvMonitorPlot)

        self.splMonitor.addWidget(self.gbMonitorPlot)

        self.verticalLayout_2.addWidget(self.splMonitor)

        self.twMain.addTab(self.tbMonitorImport, "")
        self.tbWeibull = QWidget()
        self.tbWeibull.setObjectName(u"tbWeibull")
        self.weibullLayout = QVBoxLayout(self.tbWeibull)
        self.weibullLayout.setObjectName(u"weibullLayout")
        self.splWeibull = QSplitter(self.tbWeibull)
        self.splWeibull.setObjectName(u"splWeibull")
        self.splWeibull.setOrientation(Qt.Orientation.Horizontal)
        self.gbControl = QGroupBox(self.splWeibull)
        self.gbControl.setObjectName(u"gbControl")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.gbControl.sizePolicy().hasHeightForWidth())
        self.gbControl.setSizePolicy(sizePolicy3)
        self.controlGrid = QGridLayout(self.gbControl)
        self.controlGrid.setObjectName(u"controlGrid")
        self.chkUnifySlope = QCheckBox(self.gbControl)
        self.chkUnifySlope.setObjectName(u"chkUnifySlope")

        self.controlGrid.addWidget(self.chkUnifySlope, 6, 2, 1, 1)

        self.rdoTBD = QRadioButton(self.gbControl)
        self.rdoTBD.setObjectName(u"rdoTBD")
        self.rdoTBD.setChecked(True)

        self.controlGrid.addWidget(self.rdoTBD, 6, 1, 1, 1)

        self.btnWeibullFit = QPushButton(self.gbControl)
        self.btnWeibullFit.setObjectName(u"btnWeibullFit")

        self.controlGrid.addWidget(self.btnWeibullFit, 2, 1, 1, 1)

        self.btnSelectFile = QPushButton(self.gbControl)
        self.btnSelectFile.setObjectName(u"btnSelectFile")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.btnSelectFile.sizePolicy().hasHeightForWidth())
        self.btnSelectFile.setSizePolicy(sizePolicy4)

        self.controlGrid.addWidget(self.btnSelectFile, 2, 0, 1, 1)

        self.btnSetting = QPushButton(self.gbControl)
        self.btnSetting.setObjectName(u"btnSetting")

        self.controlGrid.addWidget(self.btnSetting, 1, 1, 1, 1)

        self.lblDataType = QLabel(self.gbControl)
        self.lblDataType.setObjectName(u"lblDataType")
        self.lblDataType.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.controlGrid.addWidget(self.lblDataType, 6, 0, 2, 1)

        self.rdoQBD = QRadioButton(self.gbControl)
        self.rdoQBD.setObjectName(u"rdoQBD")

        self.controlGrid.addWidget(self.rdoQBD, 7, 1, 1, 1)

        self.btnBetaDiagnostic = QPushButton(self.gbControl)
        self.btnBetaDiagnostic.setObjectName(u"btnBetaDiagnostic")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.btnBetaDiagnostic.sizePolicy().hasHeightForWidth())
        self.btnBetaDiagnostic.setSizePolicy(sizePolicy5)

        self.controlGrid.addWidget(self.btnBetaDiagnostic, 2, 2, 1, 1)

        self.lblSheet = QLabel(self.gbControl)
        self.lblSheet.setObjectName(u"lblSheet")
        self.lblSheet.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.controlGrid.addWidget(self.lblSheet, 4, 0, 1, 1)

        self.btnAddCustomPlot = QPushButton(self.gbControl)
        self.btnAddCustomPlot.setObjectName(u"btnAddCustomPlot")
        sizePolicy5.setHeightForWidth(self.btnAddCustomPlot.sizePolicy().hasHeightForWidth())
        self.btnAddCustomPlot.setSizePolicy(sizePolicy5)

        self.controlGrid.addWidget(self.btnAddCustomPlot, 4, 2, 1, 1)

        self.twFitResult = QTabWidget(self.gbControl)
        self.twFitResult.setObjectName(u"twFitResult")
        self.tbFitResult = QWidget()
        self.tbFitResult.setObjectName(u"tbFitResult")
        self.fitResultInnerLayout = QVBoxLayout(self.tbFitResult)
        self.fitResultInnerLayout.setObjectName(u"fitResultInnerLayout")
        self.saFitResult = QScrollArea(self.tbFitResult)
        self.saFitResult.setObjectName(u"saFitResult")
        self.saFitResult.setWidgetResizable(True)
        self.saFitResultContent = QWidget()
        self.saFitResultContent.setObjectName(u"saFitResultContent")
        self.saFitResultContent.setGeometry(QRect(0, 0, 66, 16))
        self.saFitResult.setWidget(self.saFitResultContent)

        self.fitResultInnerLayout.addWidget(self.saFitResult)

        self.twFitResult.addTab(self.tbFitResult, "")
        self.tbRawData = QWidget()
        self.tbRawData.setObjectName(u"tbRawData")
        self.rawDataGrid = QGridLayout(self.tbRawData)
        self.rawDataGrid.setObjectName(u"rawDataGrid")
        self.btnRefreshData = QPushButton(self.tbRawData)
        self.btnRefreshData.setObjectName(u"btnRefreshData")

        self.rawDataGrid.addWidget(self.btnRefreshData, 0, 0, 1, 1)

        self.btnWriteData = QPushButton(self.tbRawData)
        self.btnWriteData.setObjectName(u"btnWriteData")

        self.rawDataGrid.addWidget(self.btnWriteData, 0, 1, 1, 1)

        self.tblRawData = QTableWidget(self.tbRawData)
        self.tblRawData.setObjectName(u"tblRawData")

        self.rawDataGrid.addWidget(self.tblRawData, 2, 0, 1, 2)

        self.twFitResult.addTab(self.tbRawData, "")

        self.controlGrid.addWidget(self.twFitResult, 8, 0, 1, 3)

        self.btnExportTemplate = QPushButton(self.gbControl)
        self.btnExportTemplate.setObjectName(u"btnExportTemplate")

        self.controlGrid.addWidget(self.btnExportTemplate, 1, 0, 1, 1)

        self.cmbSheetSelector = QComboBox(self.gbControl)
        self.cmbSheetSelector.setObjectName(u"cmbSheetSelector")

        self.controlGrid.addWidget(self.cmbSheetSelector, 4, 1, 1, 1)

        self.lblFilePath = QLabel(self.gbControl)
        self.lblFilePath.setObjectName(u"lblFilePath")

        self.controlGrid.addWidget(self.lblFilePath, 0, 0, 1, 3)

        self.splWeibull.addWidget(self.gbControl)
        self.gbWeibullPlot = QGroupBox(self.splWeibull)
        self.gbWeibullPlot.setObjectName(u"gbWeibullPlot")
        sizePolicy2.setHeightForWidth(self.gbWeibullPlot.sizePolicy().hasHeightForWidth())
        self.gbWeibullPlot.setSizePolicy(sizePolicy2)
        self.weibullPlotLayout = QVBoxLayout(self.gbWeibullPlot)
        self.weibullPlotLayout.setObjectName(u"weibullPlotLayout")
        self.wvWeibullPlot = QWebEngineView(self.gbWeibullPlot)
        self.wvWeibullPlot.setObjectName(u"wvWeibullPlot")
        self.wvWeibullPlot.setUrl(QUrl(u"about:blank"))

        self.weibullPlotLayout.addWidget(self.wvWeibullPlot)

        self.splWeibull.addWidget(self.gbWeibullPlot)

        self.weibullLayout.addWidget(self.splWeibull)

        self.twMain.addTab(self.tbWeibull, "")
        self.tbLifetime = QWidget()
        self.tbLifetime.setObjectName(u"tbLifetime")
        self.lifetimeLayout = QVBoxLayout(self.tbLifetime)
        self.lifetimeLayout.setObjectName(u"lifetimeLayout")
        self.splLifetime = QSplitter(self.tbLifetime)
        self.splLifetime.setObjectName(u"splLifetime")
        self.splLifetime.setOrientation(Qt.Orientation.Vertical)
        self.gbParamConfig = QGroupBox(self.splLifetime)
        self.gbParamConfig.setObjectName(u"gbParamConfig")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.gbParamConfig.sizePolicy().hasHeightForWidth())
        self.gbParamConfig.setSizePolicy(sizePolicy6)
        self.paramGrid = QGridLayout(self.gbParamConfig)
        self.paramGrid.setObjectName(u"paramGrid")
        self.btnCalc = QPushButton(self.gbParamConfig)
        self.btnCalc.setObjectName(u"btnCalc")

        self.paramGrid.addWidget(self.btnCalc, 0, 15, 1, 1)

        self.cmbTDDBModel = QComboBox(self.gbParamConfig)
        self.cmbTDDBModel.addItem("")
        self.cmbTDDBModel.addItem("")
        self.cmbTDDBModel.addItem("")
        self.cmbTDDBModel.addItem("")
        self.cmbTDDBModel.setObjectName(u"cmbTDDBModel")

        self.paramGrid.addWidget(self.cmbTDDBModel, 0, 10, 1, 1)

        self.editWorkTemp = QDoubleSpinBox(self.gbParamConfig)
        self.editWorkTemp.setObjectName(u"editWorkTemp")
        self.editWorkTemp.setDecimals(1)
        self.editWorkTemp.setMinimum(-5000.000000000000000)
        self.editWorkTemp.setMaximum(5000.000000000000000)
        self.editWorkTemp.setValue(25.000000000000000)

        self.paramGrid.addWidget(self.editWorkTemp, 0, 4, 1, 1)

        self.lblTDDBModel = QLabel(self.gbParamConfig)
        self.lblTDDBModel.setObjectName(u"lblTDDBModel")

        self.paramGrid.addWidget(self.lblTDDBModel, 0, 9, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.paramGrid.addItem(self.horizontalSpacer_3, 0, 8, 1, 1)

        self.lblOxideThickness = QLabel(self.gbParamConfig)
        self.lblOxideThickness.setObjectName(u"lblOxideThickness")

        self.paramGrid.addWidget(self.lblOxideThickness, 0, 6, 1, 1)

        self.lblPickMethod = QLabel(self.gbParamConfig)
        self.lblPickMethod.setObjectName(u"lblPickMethod")

        self.paramGrid.addWidget(self.lblPickMethod, 1, 9, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.paramGrid.addItem(self.horizontalSpacer, 0, 14, 1, 1)

        self.cmbPickMethod = QComboBox(self.gbParamConfig)
        self.cmbPickMethod.addItem("")
        self.cmbPickMethod.addItem("")
        self.cmbPickMethod.setObjectName(u"cmbPickMethod")

        self.paramGrid.addWidget(self.cmbPickMethod, 1, 10, 1, 1)

        self.editWorkVoltage = QDoubleSpinBox(self.gbParamConfig)
        self.editWorkVoltage.setObjectName(u"editWorkVoltage")
        self.editWorkVoltage.setDecimals(1)
        self.editWorkVoltage.setMinimum(-5000.000000000000000)
        self.editWorkVoltage.setMaximum(5000.000000000000000)
        self.editWorkVoltage.setValue(3.300000000000000)

        self.paramGrid.addWidget(self.editWorkVoltage, 0, 1, 1, 1)

        self.editOxideThickness = QDoubleSpinBox(self.gbParamConfig)
        self.editOxideThickness.setObjectName(u"editOxideThickness")
        self.editOxideThickness.setDecimals(1)
        self.editOxideThickness.setMinimum(-5000.000000000000000)
        self.editOxideThickness.setMaximum(5000.000000000000000)
        self.editOxideThickness.setValue(5.000000000000000)

        self.paramGrid.addWidget(self.editOxideThickness, 0, 7, 1, 1)

        self.lblWorkVoltage = QLabel(self.gbParamConfig)
        self.lblWorkVoltage.setObjectName(u"lblWorkVoltage")

        self.paramGrid.addWidget(self.lblWorkVoltage, 0, 0, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.paramGrid.addItem(self.horizontalSpacer_2, 0, 2, 1, 1)

        self.lblWorkTemp = QLabel(self.gbParamConfig)
        self.lblWorkTemp.setObjectName(u"lblWorkTemp")

        self.paramGrid.addWidget(self.lblWorkTemp, 0, 3, 1, 1)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.paramGrid.addItem(self.horizontalSpacer_4, 0, 5, 1, 1)

        self.lblStressVoltage = QLabel(self.gbParamConfig)
        self.lblStressVoltage.setObjectName(u"lblStressVoltage")

        self.paramGrid.addWidget(self.lblStressVoltage, 1, 0, 1, 1)

        self.editStressVoltage = QDoubleSpinBox(self.gbParamConfig)
        self.editStressVoltage.setObjectName(u"editStressVoltage")
        self.editStressVoltage.setDecimals(1)
        self.editStressVoltage.setMinimum(-5000.000000000000000)
        self.editStressVoltage.setMaximum(5000.000000000000000)
        self.editStressVoltage.setValue(3.300000000000000)

        self.paramGrid.addWidget(self.editStressVoltage, 1, 1, 1, 1)

        self.lblStressTemp = QLabel(self.gbParamConfig)
        self.lblStressTemp.setObjectName(u"lblStressTemp")

        self.paramGrid.addWidget(self.lblStressTemp, 1, 3, 1, 1)

        self.editStressTemp = QDoubleSpinBox(self.gbParamConfig)
        self.editStressTemp.setObjectName(u"editStressTemp")
        self.editStressTemp.setDecimals(1)
        self.editStressTemp.setMinimum(-5000.000000000000000)
        self.editStressTemp.setMaximum(5000.000000000000000)
        self.editStressTemp.setValue(25.000000000000000)

        self.paramGrid.addWidget(self.editStressTemp, 1, 4, 1, 1)

        self.splLifetime.addWidget(self.gbParamConfig)
        self.splResult = QSplitter(self.splLifetime)
        self.splResult.setObjectName(u"splResult")
        self.splResult.setOrientation(Qt.Orientation.Horizontal)
        self.twResultView = QTabWidget(self.splResult)
        self.twResultView.setObjectName(u"twResultView")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.twResultView.sizePolicy().hasHeightForWidth())
        self.twResultView.setSizePolicy(sizePolicy7)
        self.tbResult = QWidget()
        self.tbResult.setObjectName(u"tbResult")
        self.resultLayout = QVBoxLayout(self.tbResult)
        self.resultLayout.setObjectName(u"resultLayout")
        self.gbLifeResult = QGroupBox(self.tbResult)
        self.gbLifeResult.setObjectName(u"gbLifeResult")
        self.lifeGrid = QGridLayout(self.gbLifeResult)
        self.lifeGrid.setObjectName(u"lifeGrid")
        self.lblLifeFormula = QLabel(self.gbLifeResult)
        self.lblLifeFormula.setObjectName(u"lblLifeFormula")
        self.lblLifeFormula.setScaledContents(True)

        self.lifeGrid.addWidget(self.lblLifeFormula, 0, 0, 1, 1)

        self.btnLifeHelp = QToolButton(self.gbLifeResult)
        self.btnLifeHelp.setObjectName(u"btnLifeHelp")

        self.lifeGrid.addWidget(self.btnLifeHelp, 0, 2, 1, 1)

        self.btnPlotLifeFR = QPushButton(self.gbLifeResult)
        self.btnPlotLifeFR.setObjectName(u"btnPlotLifeFR")

        self.lifeGrid.addWidget(self.btnPlotLifeFR, 0, 3, 1, 1)

        self.saLifeResult = QScrollArea(self.gbLifeResult)
        self.saLifeResult.setObjectName(u"saLifeResult")
        self.saLifeResult.setWidgetResizable(True)
        self.saLifeResultContent = QWidget()
        self.saLifeResultContent.setObjectName(u"saLifeResultContent")
        self.saLifeResultContent.setGeometry(QRect(0, 0, 114, 88))
        self.horizontalLayout = QHBoxLayout(self.saLifeResultContent)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.tblLifeResult = QTableView(self.saLifeResultContent)
        self.tblLifeResult.setObjectName(u"tblLifeResult")

        self.horizontalLayout.addWidget(self.tblLifeResult)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.horizontalLayout.addItem(self.verticalSpacer)

        self.saLifeResult.setWidget(self.saLifeResultContent)

        self.lifeGrid.addWidget(self.saLifeResult, 1, 0, 1, 4)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.lifeGrid.addItem(self.horizontalSpacer_5, 0, 1, 1, 1)


        self.resultLayout.addWidget(self.gbLifeResult)

        self.gbFailResult = QGroupBox(self.tbResult)
        self.gbFailResult.setObjectName(u"gbFailResult")
        self.failGrid = QGridLayout(self.gbFailResult)
        self.failGrid.setObjectName(u"failGrid")
        self.saFailResult = QScrollArea(self.gbFailResult)
        self.saFailResult.setObjectName(u"saFailResult")
        self.saFailResult.setWidgetResizable(True)
        self.saFailResultContent = QWidget()
        self.saFailResultContent.setObjectName(u"saFailResultContent")
        self.saFailResultContent.setGeometry(QRect(0, 0, 114, 88))
        self.horizontalLayout_2 = QHBoxLayout(self.saFailResultContent)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.tblFailResult = QTableView(self.saFailResultContent)
        self.tblFailResult.setObjectName(u"tblFailResult")

        self.horizontalLayout_2.addWidget(self.tblFailResult)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.horizontalLayout_2.addItem(self.verticalSpacer_2)

        self.saFailResult.setWidget(self.saFailResultContent)

        self.failGrid.addWidget(self.saFailResult, 1, 0, 1, 4)

        self.btnPlotFailCurve = QPushButton(self.gbFailResult)
        self.btnPlotFailCurve.setObjectName(u"btnPlotFailCurve")

        self.failGrid.addWidget(self.btnPlotFailCurve, 0, 3, 1, 1)

        self.lblFailFormula = QLabel(self.gbFailResult)
        self.lblFailFormula.setObjectName(u"lblFailFormula")
        self.lblFailFormula.setScaledContents(True)

        self.failGrid.addWidget(self.lblFailFormula, 0, 0, 1, 1)

        self.btnFailHelp = QToolButton(self.gbFailResult)
        self.btnFailHelp.setObjectName(u"btnFailHelp")

        self.failGrid.addWidget(self.btnFailHelp, 0, 2, 1, 1)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.failGrid.addItem(self.horizontalSpacer_6, 0, 1, 1, 1)


        self.resultLayout.addWidget(self.gbFailResult)

        self.gbModelParameter = QGroupBox(self.tbResult)
        self.gbModelParameter.setObjectName(u"gbModelParameter")
        self.failGrid_2 = QGridLayout(self.gbModelParameter)
        self.failGrid_2.setObjectName(u"failGrid_2")
        self.saModelParameter = QScrollArea(self.gbModelParameter)
        self.saModelParameter.setObjectName(u"saModelParameter")
        self.saModelParameter.setWidgetResizable(True)
        self.saModelParameterContent = QWidget()
        self.saModelParameterContent.setObjectName(u"saModelParameterContent")
        self.saModelParameterContent.setGeometry(QRect(0, 0, 114, 88))
        self.horizontalLayout_3 = QHBoxLayout(self.saModelParameterContent)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.tblModelParameter = QTableView(self.saModelParameterContent)
        self.tblModelParameter.setObjectName(u"tblModelParameter")

        self.horizontalLayout_3.addWidget(self.tblModelParameter)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.horizontalLayout_3.addItem(self.verticalSpacer_3)

        self.saModelParameter.setWidget(self.saModelParameterContent)

        self.failGrid_2.addWidget(self.saModelParameter, 0, 0, 1, 2)


        self.resultLayout.addWidget(self.gbModelParameter)

        self.twResultView.addTab(self.tbResult, "")
        self.tbRawParams = QWidget()
        self.tbRawParams.setObjectName(u"tbRawParams")
        self.rawParamsLayout = QVBoxLayout(self.tbRawParams)
        self.rawParamsLayout.setObjectName(u"rawParamsLayout")
        self.tblRawParams = QTableWidget(self.tbRawParams)
        self.tblRawParams.setObjectName(u"tblRawParams")

        self.rawParamsLayout.addWidget(self.tblRawParams)

        self.twResultView.addTab(self.tbRawParams, "")
        self.splResult.addWidget(self.twResultView)
        self.gbModelPlot = QGroupBox(self.splResult)
        self.gbModelPlot.setObjectName(u"gbModelPlot")
        sizePolicy2.setHeightForWidth(self.gbModelPlot.sizePolicy().hasHeightForWidth())
        self.gbModelPlot.setSizePolicy(sizePolicy2)
        self.modelPlotLayout = QVBoxLayout(self.gbModelPlot)
        self.modelPlotLayout.setObjectName(u"modelPlotLayout")
        self.wvModelPlot = QWebEngineView(self.gbModelPlot)
        self.wvModelPlot.setObjectName(u"wvModelPlot")
        self.wvModelPlot.setUrl(QUrl(u"about:blank"))

        self.modelPlotLayout.addWidget(self.wvModelPlot)

        self.splResult.addWidget(self.gbModelPlot)
        self.splLifetime.addWidget(self.splResult)

        self.lifetimeLayout.addWidget(self.splLifetime)

        self.twMain.addTab(self.tbLifetime, "")

        self.mainLayout.addWidget(self.twMain)


        self.retranslateUi(Form)

        self.twMain.setCurrentIndex(0)
        self.twFitResult.setCurrentIndex(0)
        self.twResultView.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.gbFileHandling.setTitle(QCoreApplication.translate("Form", u"\u6587\u4ef6\u5904\u7406", None))
        self.btnRemoveAll.setText(QCoreApplication.translate("Form", u"\u5168\u90e8\u5220\u9664", None))
        self.btnRemoveSelected.setText(QCoreApplication.translate("Form", u"\u5220\u9664\u9009\u4e2d", None))
        self.btnAddFile.setText(QCoreApplication.translate("Form", u"\u6dfb\u52a0\u6587\u4ef6", None))
        self.gbPreviewConfig.setTitle(QCoreApplication.translate("Form", u"\u6570\u636e\u9884\u89c8", None))
        self.lblRateLimit.setText(QCoreApplication.translate("Form", u"\u500d\u7387\u4e0a\u9650\uff1a", None))
        self.btnExportData.setText(QCoreApplication.translate("Form", u"\u5bfc\u51fa\u6570\u636e", None))
        self.chkFailCurrentDrop.setText(QCoreApplication.translate("Form", u"\u76d1\u63a7\u7535\u6d41\u964d\u4e3a0", None))
        self.chklogY.setText(QCoreApplication.translate("Form", u"Y\u8f74\u4f7f\u7528\u5bf9\u6570\u5750\u6807\u7cfb", None))
        self.chkFailCurrentLimit.setText(QCoreApplication.translate("Form", u"\u8d85\u8fc7\u8bbe\u5b9a\u7535\u6d41\u4e0a\u9650", None))
        self.lblCurrentLimit.setText(QCoreApplication.translate("Form", u"\u7535\u6d41\u4e0a\u9650/uA:", None))
        self.chkFailHalfTime.setText(QCoreApplication.translate("Form", u"\u6392\u9664\u8d85\u8fc7\u4e00\u534a\u540c\u65f6\u5931\u6548\u65f6\u95f4", None))
        self.btnToWeibullFit.setText(QCoreApplication.translate("Form", u"\u4f7f\u7528\u5f53\u524d\u6570\u636e\u524d\u5f80Weibull\u5206\u5e03\u62df\u5408", None))
        self.lblFailLogic.setText(QCoreApplication.translate("Form", u"\u5931\u6548\u70b9\u5224\u65ad\u903b\u8f91\uff1a", None))
        self.chkFailRateExceed.setText(QCoreApplication.translate("Form", u"\u76f8\u8f83\u524d\u4e00\u65f6\u523b\u500d\u7387\u8d85\u9650", None))
        self.chklogX.setText(QCoreApplication.translate("Form", u"X\u8f74\u4f7f\u7528\u5bf9\u6570\u5750\u6807\u7cfb", None))
        self.lblPreviewFile.setText(QCoreApplication.translate("Form", u"\u9884\u89c8\u6587\u4ef6\u9009\u62e9\uff1a", None))
        self.gbMonitorPlot.setTitle(QCoreApplication.translate("Form", u"\u76d1\u63a7\u6570\u636e\u9884\u89c8", None))
        self.twMain.setTabText(self.twMain.indexOf(self.tbMonitorImport), QCoreApplication.translate("Form", u"\u76d1\u63a7\u6570\u636e\u63d0\u53d6", None))
        self.gbControl.setTitle(QCoreApplication.translate("Form", u"\u63a7\u5236", None))
        self.chkUnifySlope.setText(QCoreApplication.translate("Form", u"\u542f\u7528\u7edf\u4e00\u659c\u7387", None))
        self.rdoTBD.setText(QCoreApplication.translate("Form", u"TBD", None))
        self.btnWeibullFit.setText(QCoreApplication.translate("Form", u"weibull\u62df\u5408", None))
        self.btnSelectFile.setText(QCoreApplication.translate("Form", u"\u9009\u62e9\u6570\u636e", None))
        self.btnSetting.setText(QCoreApplication.translate("Form", u"\u8bbe\u7f6e", None))
        self.lblDataType.setText(QCoreApplication.translate("Form", u"\u8ba1\u7b97\u6570\u636e\uff1a", None))
        self.rdoQBD.setText(QCoreApplication.translate("Form", u"QBD", None))
        self.btnBetaDiagnostic.setText(QCoreApplication.translate("Form", u"\u03b2\u8bca\u65ad", None))
        self.lblSheet.setText(QCoreApplication.translate("Form", u"\u9009\u62e9sheet\uff1a", None))
        self.btnAddCustomPlot.setText(QCoreApplication.translate("Form", u"\u6dfb\u52a0\u81ea\u5b9a\u4e49\u56fe", None))
        self.twFitResult.setTabText(self.twFitResult.indexOf(self.tbFitResult), QCoreApplication.translate("Form", u"\u62df\u5408\u7ed3\u679c", None))
        self.btnRefreshData.setText(QCoreApplication.translate("Form", u"\u5237\u65b0", None))
        self.btnWriteData.setText(QCoreApplication.translate("Form", u"\u5199\u5165", None))
        self.twFitResult.setTabText(self.twFitResult.indexOf(self.tbRawData), QCoreApplication.translate("Form", u"\u539f\u59cb\u6570\u636e", None))
        self.btnExportTemplate.setText(QCoreApplication.translate("Form", u"\u5bfc\u51fa\u6a21\u677f", None))
        self.lblFilePath.setText(QCoreApplication.translate("Form", u"\u5f85\u9009\u62e9\u6587\u4ef6...", None))
        self.gbWeibullPlot.setTitle(QCoreApplication.translate("Form", u"\u7ed3\u679c\u663e\u793a", None))
        self.twMain.setTabText(self.twMain.indexOf(self.tbWeibull), QCoreApplication.translate("Form", u"weibull\u5206\u5e03\u62df\u5408", None))
        self.gbParamConfig.setTitle(QCoreApplication.translate("Form", u"\u53c2\u6570\u914d\u7f6e", None))
        self.btnCalc.setText(QCoreApplication.translate("Form", u"\u8ba1\u7b97", None))
        self.cmbTDDBModel.setItemText(0, QCoreApplication.translate("Form", u"E\u6a21\u578b", None))
        self.cmbTDDBModel.setItemText(1, QCoreApplication.translate("Form", u"1/E\u6a21\u578b", None))
        self.cmbTDDBModel.setItemText(2, QCoreApplication.translate("Form", u"V\u6a21\u578b", None))
        self.cmbTDDBModel.setItemText(3, QCoreApplication.translate("Form", u"\u221aE\u6a21\u578b", None))

        self.lblTDDBModel.setText(QCoreApplication.translate("Form", u"TDDB\u6a21\u578b\uff1a", None))
        self.lblOxideThickness.setText(QCoreApplication.translate("Form", u"\u6805\u6c27\u539a\u5ea6/nm\uff1a", None))
        self.lblPickMethod.setText(QCoreApplication.translate("Form", u"\u53d6\u70b9\u65b9\u5f0f\uff1a", None))
        self.cmbPickMethod.setItemText(0, QCoreApplication.translate("Form", u"weibull\u66f2\u7ebf\u53d6\u70b9", None))
        self.cmbPickMethod.setItemText(1, QCoreApplication.translate("Form", u"\u539f\u59cb\u6570\u636e\u5e73\u6ed1\u53d6\u70b9", None))

        self.lblWorkVoltage.setText(QCoreApplication.translate("Form", u"\u5de5\u4f5c\u7535\u538b/V\uff1a", None))
        self.lblWorkTemp.setText(QCoreApplication.translate("Form", u"\u5de5\u4f5c\u6e29\u5ea6/\u2103\uff1a", None))
        self.lblStressVoltage.setText(QCoreApplication.translate("Form", u"\u8001\u5316\u7535\u538b/V\uff1a", None))
        self.lblStressTemp.setText(QCoreApplication.translate("Form", u"\u8001\u5316\u6e29\u5ea6/\u2103\uff1a", None))
        self.gbLifeResult.setTitle(QCoreApplication.translate("Form", u"\u5bff\u547d\u8ba1\u7b97", None))
        self.lblLifeFormula.setText(QCoreApplication.translate("Form", u"\u8ba1\u7b97\u516c\u5f0f\uff1a", None))
        self.btnLifeHelp.setText(QCoreApplication.translate("Form", u"\uff1f", None))
        self.btnPlotLifeFR.setText(QCoreApplication.translate("Form", u"\u7ed8\u5236\u5bff\u547d-\u5931\u6548\u7387\u66f2\u7ebf", None))
        self.gbFailResult.setTitle(QCoreApplication.translate("Form", u"\u5931\u6548\u7387\u8ba1\u7b97", None))
        self.btnPlotFailCurve.setText(QCoreApplication.translate("Form", u"\u7ed8\u5236\u5931\u6548\u7387-\u5de5\u4f5c\u65f6\u95f4\u66f2\u7ebf", None))
        self.lblFailFormula.setText(QCoreApplication.translate("Form", u"\u8ba1\u7b97\u516c\u5f0f\uff1a", None))
        self.btnFailHelp.setText(QCoreApplication.translate("Form", u"\uff1f", None))
        self.gbModelParameter.setTitle(QCoreApplication.translate("Form", u"\u6a21\u578b\u53c2\u6570\u7ed3\u679c", None))
        self.twResultView.setTabText(self.twResultView.indexOf(self.tbResult), QCoreApplication.translate("Form", u"\u7ed3\u679c\u663e\u793a", None))
        self.twResultView.setTabText(self.twResultView.indexOf(self.tbRawParams), QCoreApplication.translate("Form", u"\u8ba1\u7b97\u6570\u636e\u67e5\u770b", None))
        self.gbModelPlot.setTitle(QCoreApplication.translate("Form", u"\u6a21\u578b\u7ed8\u56fe", None))
        self.twMain.setTabText(self.twMain.indexOf(self.tbLifetime), QCoreApplication.translate("Form", u"\u5bff\u547d\u8ba1\u7b97", None))
    # retranslateUi

