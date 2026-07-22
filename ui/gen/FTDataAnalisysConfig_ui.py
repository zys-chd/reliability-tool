# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'FTDataAnalisysConfig.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QRadioButton, QScrollArea, QSizePolicy, QSpacerItem,
    QSpinBox, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_ConfigDialog(object):
    def setupUi(self, ConfigDialog):
        if not ConfigDialog.objectName():
            ConfigDialog.setObjectName(u"ConfigDialog")
        ConfigDialog.resize(1146, 1185)
        self.gridLayout = QGridLayout(ConfigDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gbConfigSelect = QGroupBox(ConfigDialog)
        self.gbConfigSelect.setObjectName(u"gbConfigSelect")
        self.gridLayout_4 = QGridLayout(self.gbConfigSelect)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.cmbConfig = QComboBox(self.gbConfigSelect)
        self.cmbConfig.setObjectName(u"cmbConfig")

        self.gridLayout_4.addWidget(self.cmbConfig, 1, 2, 1, 1)

        self.btnConfigFileSelect = QPushButton(self.gbConfigSelect)
        self.btnConfigFileSelect.setObjectName(u"btnConfigFileSelect")

        self.gridLayout_4.addWidget(self.btnConfigFileSelect, 0, 2, 1, 1)

        self.lblAddConfig = QLabel(self.gbConfigSelect)
        self.lblAddConfig.setObjectName(u"lblAddConfig")

        self.gridLayout_4.addWidget(self.lblAddConfig, 1, 5, 1, 1)

        self.btnAddConfig = QPushButton(self.gbConfigSelect)
        self.btnAddConfig.setObjectName(u"btnAddConfig")

        self.gridLayout_4.addWidget(self.btnAddConfig, 1, 7, 1, 1)

        self.lblConfig = QLabel(self.gbConfigSelect)
        self.lblConfig.setObjectName(u"lblConfig")

        self.gridLayout_4.addWidget(self.lblConfig, 1, 1, 1, 1)

        self.editNewConfig = QLineEdit(self.gbConfigSelect)
        self.editNewConfig.setObjectName(u"editNewConfig")

        self.gridLayout_4.addWidget(self.editNewConfig, 1, 6, 1, 1)

        self.spacerConfig = QSpacerItem(285, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_4.addItem(self.spacerConfig, 1, 3, 1, 2)

        self.lblCurrentConfigFile = QLabel(self.gbConfigSelect)
        self.lblCurrentConfigFile.setObjectName(u"lblCurrentConfigFile")

        self.gridLayout_4.addWidget(self.lblCurrentConfigFile, 0, 3, 1, 5)


        self.gridLayout.addWidget(self.gbConfigSelect, 0, 0, 1, 1)

        self.tabConfig = QTabWidget(ConfigDialog)
        self.tabConfig.setObjectName(u"tabConfig")
        self.tabConfig.setTabPosition(QTabWidget.TabPosition.West)
        self.tabGroup = QWidget()
        self.tabGroup.setObjectName(u"tabGroup")
        self.vlGroup = QVBoxLayout(self.tabGroup)
        self.vlGroup.setObjectName(u"vlGroup")
        self.tabGroupMode = QTabWidget(self.tabGroup)
        self.tabGroupMode.setObjectName(u"tabGroupMode")
        self.tabByName = QWidget()
        self.tabByName.setObjectName(u"tabByName")
        self.vlFilenameGroup = QVBoxLayout(self.tabByName)
        self.vlFilenameGroup.setObjectName(u"vlFilenameGroup")
        self.frameFilenameGroup = QFrame(self.tabByName)
        self.frameFilenameGroup.setObjectName(u"frameFilenameGroup")
        self.frameFilenameGroup.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameFilenameGroup.setFrameShadow(QFrame.Shadow.Raised)
        self.vlFilenameFrame = QVBoxLayout(self.frameFilenameGroup)
        self.vlFilenameFrame.setObjectName(u"vlFilenameFrame")
        self.scrollFilenameGroup = QScrollArea(self.frameFilenameGroup)
        self.scrollFilenameGroup.setObjectName(u"scrollFilenameGroup")
        self.scrollFilenameGroup.setWidgetResizable(True)
        self.scrollFilenameContent = QWidget()
        self.scrollFilenameContent.setObjectName(u"scrollFilenameContent")
        self.scrollFilenameContent.setGeometry(QRect(0, 0, 98, 28))
        self.scrollFilenameGroup.setWidget(self.scrollFilenameContent)

        self.vlFilenameFrame.addWidget(self.scrollFilenameGroup)


        self.vlFilenameGroup.addWidget(self.frameFilenameGroup)

        self.tabGroupMode.addTab(self.tabByName, "")
        self.tabBySN = QWidget()
        self.tabBySN.setObjectName(u"tabBySN")
        self.gridLayout_2 = QGridLayout(self.tabBySN)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.btnClearSN = QPushButton(self.tabBySN)
        self.btnClearSN.setObjectName(u"btnClearSN")

        self.gridLayout_2.addWidget(self.btnClearSN, 0, 1, 1, 1)

        self.btnPasteSN = QPushButton(self.tabBySN)
        self.btnPasteSN.setObjectName(u"btnPasteSN")

        self.gridLayout_2.addWidget(self.btnPasteSN, 0, 0, 1, 1)

        self.tblSN = QTableWidget(self.tabBySN)
        self.tblSN.setObjectName(u"tblSN")

        self.gridLayout_2.addWidget(self.tblSN, 1, 0, 1, 2)

        self.tabGroupMode.addTab(self.tabBySN, "")

        self.vlGroup.addWidget(self.tabGroupMode)

        self.gbGroupMode = QGroupBox(self.tabGroup)
        self.gbGroupMode.setObjectName(u"gbGroupMode")
        self.hlGroupMode = QHBoxLayout(self.gbGroupMode)
        self.hlGroupMode.setObjectName(u"hlGroupMode")
        self.rbByName = QRadioButton(self.gbGroupMode)
        self.rbByName.setObjectName(u"rbByName")
        self.rbByName.setChecked(True)

        self.hlGroupMode.addWidget(self.rbByName)

        self.rbBySN = QRadioButton(self.gbGroupMode)
        self.rbBySN.setObjectName(u"rbBySN")
        self.rbBySN.setChecked(False)

        self.hlGroupMode.addWidget(self.rbBySN)

        self.rbBoth = QRadioButton(self.gbGroupMode)
        self.rbBoth.setObjectName(u"rbBoth")

        self.hlGroupMode.addWidget(self.rbBoth)


        self.vlGroup.addWidget(self.gbGroupMode)

        self.tabConfig.addTab(self.tabGroup, "")
        self.tabTemplate = QWidget()
        self.tabTemplate.setObjectName(u"tabTemplate")
        self.vlTemplate = QVBoxLayout(self.tabTemplate)
        self.vlTemplate.setObjectName(u"vlTemplate")
        self.tabTemplateMode = QTabWidget(self.tabTemplate)
        self.tabTemplateMode.setObjectName(u"tabTemplateMode")
        self.tabTemplateFile = QWidget()
        self.tabTemplateFile.setObjectName(u"tabTemplateFile")
        self.glTemplate = QGridLayout(self.tabTemplateFile)
        self.glTemplate.setObjectName(u"glTemplate")
        self.lblCachePath = QLabel(self.tabTemplateFile)
        self.lblCachePath.setObjectName(u"lblCachePath")

        self.glTemplate.addWidget(self.lblCachePath, 0, 0, 1, 1)

        self.btnSelectTemplate = QPushButton(self.tabTemplateFile)
        self.btnSelectTemplate.setObjectName(u"btnSelectTemplate")

        self.glTemplate.addWidget(self.btnSelectTemplate, 1, 3, 1, 1)

        self.gbPreview = QGroupBox(self.tabTemplateFile)
        self.gbPreview.setObjectName(u"gbPreview")
        self.vlPreview = QVBoxLayout(self.gbPreview)
        self.vlPreview.setObjectName(u"vlPreview")
        self.scrollPreview = QScrollArea(self.gbPreview)
        self.scrollPreview.setObjectName(u"scrollPreview")
        self.scrollPreview.setWidgetResizable(True)
        self.scrollPreviewContent = QWidget()
        self.scrollPreviewContent.setObjectName(u"scrollPreviewContent")
        self.scrollPreviewContent.setGeometry(QRect(0, 0, 1029, 800))
        self.glPreview = QGridLayout(self.scrollPreviewContent)
        self.glPreview.setObjectName(u"glPreview")
        self.tabPreview = QTabWidget(self.scrollPreviewContent)
        self.tabPreview.setObjectName(u"tabPreview")

        self.glPreview.addWidget(self.tabPreview, 0, 0, 1, 1)

        self.scrollPreview.setWidget(self.scrollPreviewContent)

        self.vlPreview.addWidget(self.scrollPreview)


        self.glTemplate.addWidget(self.gbPreview, 2, 0, 1, 4)

        self.btnOpenCachePath = QPushButton(self.tabTemplateFile)
        self.btnOpenCachePath.setObjectName(u"btnOpenCachePath")

        self.glTemplate.addWidget(self.btnOpenCachePath, 0, 2, 1, 1)

        self.lblTemplatePath = QLabel(self.tabTemplateFile)
        self.lblTemplatePath.setObjectName(u"lblTemplatePath")

        self.glTemplate.addWidget(self.lblTemplatePath, 1, 0, 1, 1)

        self.btnSelectCachePath = QPushButton(self.tabTemplateFile)
        self.btnSelectCachePath.setObjectName(u"btnSelectCachePath")

        self.glTemplate.addWidget(self.btnSelectCachePath, 0, 3, 1, 1)

        self.editTemplatePath = QLineEdit(self.tabTemplateFile)
        self.editTemplatePath.setObjectName(u"editTemplatePath")

        self.glTemplate.addWidget(self.editTemplatePath, 1, 1, 1, 1)

        self.btnOpenTemplate = QPushButton(self.tabTemplateFile)
        self.btnOpenTemplate.setObjectName(u"btnOpenTemplate")

        self.glTemplate.addWidget(self.btnOpenTemplate, 1, 2, 1, 1)

        self.editCachePath = QLineEdit(self.tabTemplateFile)
        self.editCachePath.setObjectName(u"editCachePath")

        self.glTemplate.addWidget(self.editCachePath, 0, 1, 1, 1)

        self.tabTemplateMode.addTab(self.tabTemplateFile, "")
        self.tabTestItems = QWidget()
        self.tabTestItems.setObjectName(u"tabTestItems")
        self.gridLayout_3 = QGridLayout(self.tabTestItems)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gbFilter = QGroupBox(self.tabTestItems)
        self.gbFilter.setObjectName(u"gbFilter")
        self.hlFilter = QHBoxLayout(self.gbFilter)
        self.hlFilter.setObjectName(u"hlFilter")
        self.lblInclude = QLabel(self.gbFilter)
        self.lblInclude.setObjectName(u"lblInclude")

        self.hlFilter.addWidget(self.lblInclude)

        self.editInclude = QLineEdit(self.gbFilter)
        self.editInclude.setObjectName(u"editInclude")

        self.hlFilter.addWidget(self.editInclude)

        self.lblExclude = QLabel(self.gbFilter)
        self.lblExclude.setObjectName(u"lblExclude")

        self.hlFilter.addWidget(self.lblExclude)

        self.editExclude = QLineEdit(self.gbFilter)
        self.editExclude.setObjectName(u"editExclude")

        self.hlFilter.addWidget(self.editExclude)

        self.spacerFilter = QSpacerItem(212, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlFilter.addItem(self.spacerFilter)


        self.gridLayout_3.addWidget(self.gbFilter, 0, 0, 1, 1)

        self.splitterTestItems = QSplitter(self.tabTestItems)
        self.splitterTestItems.setObjectName(u"splitterTestItems")
        self.splitterTestItems.setOrientation(Qt.Orientation.Horizontal)
        self.gbOrigin = QGroupBox(self.splitterTestItems)
        self.gbOrigin.setObjectName(u"gbOrigin")
        self.glOrigin = QGridLayout(self.gbOrigin)
        self.glOrigin.setObjectName(u"glOrigin")
        self.scrollOrigin = QScrollArea(self.gbOrigin)
        self.scrollOrigin.setObjectName(u"scrollOrigin")
        self.scrollOrigin.setWidgetResizable(True)
        self.scrollOriginContent = QWidget()
        self.scrollOriginContent.setObjectName(u"scrollOriginContent")
        self.scrollOriginContent.setGeometry(QRect(0, 0, 98, 28))
        self.scrollOrigin.setWidget(self.scrollOriginContent)

        self.glOrigin.addWidget(self.scrollOrigin, 0, 0, 1, 1)

        self.splitterTestItems.addWidget(self.gbOrigin)
        self.gbCandidate = QGroupBox(self.splitterTestItems)
        self.gbCandidate.setObjectName(u"gbCandidate")
        self.glCandidate = QGridLayout(self.gbCandidate)
        self.glCandidate.setObjectName(u"glCandidate")
        self.scrollCandidate = QScrollArea(self.gbCandidate)
        self.scrollCandidate.setObjectName(u"scrollCandidate")
        self.scrollCandidate.setWidgetResizable(True)
        self.scrollCandidateContent = QWidget()
        self.scrollCandidateContent.setObjectName(u"scrollCandidateContent")
        self.scrollCandidateContent.setGeometry(QRect(0, 0, 98, 28))
        self.scrollCandidate.setWidget(self.scrollCandidateContent)

        self.glCandidate.addWidget(self.scrollCandidate, 0, 0, 1, 1)

        self.splitterTestItems.addWidget(self.gbCandidate)
        self.frameMoveButtons = QFrame(self.splitterTestItems)
        self.frameMoveButtons.setObjectName(u"frameMoveButtons")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frameMoveButtons.sizePolicy().hasHeightForWidth())
        self.frameMoveButtons.setSizePolicy(sizePolicy)
        self.frameMoveButtons.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameMoveButtons.setFrameShadow(QFrame.Shadow.Raised)
        self.vlMoveButtons = QVBoxLayout(self.frameMoveButtons)
        self.vlMoveButtons.setObjectName(u"vlMoveButtons")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlMoveButtons.addItem(self.verticalSpacer_2)

        self.btnMoveRight = QPushButton(self.frameMoveButtons)
        self.btnMoveRight.setObjectName(u"btnMoveRight")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btnMoveRight.sizePolicy().hasHeightForWidth())
        self.btnMoveRight.setSizePolicy(sizePolicy1)

        self.vlMoveButtons.addWidget(self.btnMoveRight)

        self.btnMoveLeft = QPushButton(self.frameMoveButtons)
        self.btnMoveLeft.setObjectName(u"btnMoveLeft")

        self.vlMoveButtons.addWidget(self.btnMoveLeft)

        self.btnMoveAllRight = QPushButton(self.frameMoveButtons)
        self.btnMoveAllRight.setObjectName(u"btnMoveAllRight")

        self.vlMoveButtons.addWidget(self.btnMoveAllRight)

        self.btnMoveAllLeft = QPushButton(self.frameMoveButtons)
        self.btnMoveAllLeft.setObjectName(u"btnMoveAllLeft")

        self.vlMoveButtons.addWidget(self.btnMoveAllLeft)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlMoveButtons.addItem(self.verticalSpacer_3)

        self.splitterTestItems.addWidget(self.frameMoveButtons)
        self.gbSelected = QGroupBox(self.splitterTestItems)
        self.gbSelected.setObjectName(u"gbSelected")
        self.glSelected = QGridLayout(self.gbSelected)
        self.glSelected.setObjectName(u"glSelected")
        self.scrollSelected = QScrollArea(self.gbSelected)
        self.scrollSelected.setObjectName(u"scrollSelected")
        self.scrollSelected.setWidgetResizable(True)
        self.scrollSelectedContent = QWidget()
        self.scrollSelectedContent.setObjectName(u"scrollSelectedContent")
        self.scrollSelectedContent.setGeometry(QRect(0, 0, 98, 28))
        self.scrollSelected.setWidget(self.scrollSelectedContent)

        self.glSelected.addWidget(self.scrollSelected, 0, 0, 1, 1)

        self.splitterTestItems.addWidget(self.gbSelected)

        self.gridLayout_3.addWidget(self.splitterTestItems, 1, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer, 1, 1, 1, 1)

        self.tabTemplateMode.addTab(self.tabTestItems, "")
        self.tabCalcLimit = QWidget()
        self.tabCalcLimit.setObjectName(u"tabCalcLimit")
        self.vlCalc = QVBoxLayout(self.tabCalcLimit)
        self.vlCalc.setObjectName(u"vlCalc")
        self.gbCalcFilter = QGroupBox(self.tabCalcLimit)
        self.gbCalcFilter.setObjectName(u"gbCalcFilter")
        self.glCalcFilter = QGridLayout(self.gbCalcFilter)
        self.glCalcFilter.setObjectName(u"glCalcFilter")
        self.lblCalcInclude = QLabel(self.gbCalcFilter)
        self.lblCalcInclude.setObjectName(u"lblCalcInclude")

        self.glCalcFilter.addWidget(self.lblCalcInclude, 0, 0, 1, 1)

        self.editCalcInclude = QLineEdit(self.gbCalcFilter)
        self.editCalcInclude.setObjectName(u"editCalcInclude")

        self.glCalcFilter.addWidget(self.editCalcInclude, 0, 1, 1, 1)

        self.lblCalcExclude = QLabel(self.gbCalcFilter)
        self.lblCalcExclude.setObjectName(u"lblCalcExclude")

        self.glCalcFilter.addWidget(self.lblCalcExclude, 0, 2, 1, 1)

        self.editCalcExclude = QLineEdit(self.gbCalcFilter)
        self.editCalcExclude.setObjectName(u"editCalcExclude")

        self.glCalcFilter.addWidget(self.editCalcExclude, 0, 3, 1, 1)


        self.vlCalc.addWidget(self.gbCalcFilter)

        self.gbCalcBatch = QGroupBox(self.tabCalcLimit)
        self.gbCalcBatch.setObjectName(u"gbCalcBatch")
        self.glCalcBatch = QGridLayout(self.gbCalcBatch)
        self.glCalcBatch.setObjectName(u"glCalcBatch")
        self.btnCalcApply = QPushButton(self.gbCalcBatch)
        self.btnCalcApply.setObjectName(u"btnCalcApply")

        self.glCalcBatch.addWidget(self.btnCalcApply, 0, 11, 1, 1)

        self.lblCalcRename = QLabel(self.gbCalcBatch)
        self.lblCalcRename.setObjectName(u"lblCalcRename")

        self.glCalcBatch.addWidget(self.lblCalcRename, 0, 7, 1, 1)

        self.editCalcRenameSuffix = QLineEdit(self.gbCalcBatch)
        self.editCalcRenameSuffix.setObjectName(u"editCalcRenameSuffix")

        self.glCalcBatch.addWidget(self.editCalcRenameSuffix, 0, 10, 1, 1)

        self.lblCalcPreset = QLabel(self.gbCalcBatch)
        self.lblCalcPreset.setObjectName(u"lblCalcPreset")

        self.glCalcBatch.addWidget(self.lblCalcPreset, 0, 1, 1, 1)

        self.spacerCalcBatch = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.glCalcBatch.addItem(self.spacerCalcBatch, 0, 12, 1, 1)

        self.lblCalcRenameSuffix = QLabel(self.gbCalcBatch)
        self.lblCalcRenameSuffix.setObjectName(u"lblCalcRenameSuffix")

        self.glCalcBatch.addWidget(self.lblCalcRenameSuffix, 0, 9, 1, 1)

        self.cmbCalcPreset = QComboBox(self.gbCalcBatch)
        self.cmbCalcPreset.addItem("")
        self.cmbCalcPreset.addItem("")
        self.cmbCalcPreset.addItem("")
        self.cmbCalcPreset.setObjectName(u"cmbCalcPreset")

        self.glCalcBatch.addWidget(self.cmbCalcPreset, 0, 2, 1, 1)

        self.editCalcRename = QLineEdit(self.gbCalcBatch)
        self.editCalcRename.setObjectName(u"editCalcRename")

        self.glCalcBatch.addWidget(self.editCalcRename, 0, 8, 1, 1)

        self.editCalcLimit = QLineEdit(self.gbCalcBatch)
        self.editCalcLimit.setObjectName(u"editCalcLimit")

        self.glCalcBatch.addWidget(self.editCalcLimit, 0, 4, 1, 1)

        self.cmbCalcLimitDir = QComboBox(self.gbCalcBatch)
        self.cmbCalcLimitDir.addItem("")
        self.cmbCalcLimitDir.addItem("")
        self.cmbCalcLimitDir.setObjectName(u"cmbCalcLimitDir")

        self.glCalcBatch.addWidget(self.cmbCalcLimitDir, 0, 6, 1, 1)

        self.lblCalcLimit = QLabel(self.gbCalcBatch)
        self.lblCalcLimit.setObjectName(u"lblCalcLimit")

        self.glCalcBatch.addWidget(self.lblCalcLimit, 0, 3, 1, 1)

        self.lblCalcLimitDir = QLabel(self.gbCalcBatch)
        self.lblCalcLimitDir.setObjectName(u"lblCalcLimitDir")

        self.glCalcBatch.addWidget(self.lblCalcLimitDir, 0, 5, 1, 1)

        self.btnFormulaManage = QPushButton(self.gbCalcBatch)
        self.btnFormulaManage.setObjectName(u"btnFormulaManage")

        self.glCalcBatch.addWidget(self.btnFormulaManage, 0, 0, 1, 1)


        self.vlCalc.addWidget(self.gbCalcBatch)

        self.gbCalcTable = QGroupBox(self.tabCalcLimit)
        self.gbCalcTable.setObjectName(u"gbCalcTable")
        self.verticalLayout = QVBoxLayout(self.gbCalcTable)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollCalcTable = QScrollArea(self.gbCalcTable)
        self.scrollCalcTable.setObjectName(u"scrollCalcTable")
        self.scrollCalcTable.setWidgetResizable(True)
        self.scrollCalcTableContent = QWidget()
        self.scrollCalcTableContent.setObjectName(u"scrollCalcTableContent")
        self.scrollCalcTableContent.setGeometry(QRect(0, 0, 98, 88))
        self.verticalLayout_3 = QVBoxLayout(self.scrollCalcTableContent)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.tblCalcConfig = QTableWidget(self.scrollCalcTableContent)
        self.tblCalcConfig.setObjectName(u"tblCalcConfig")

        self.verticalLayout_3.addWidget(self.tblCalcConfig)

        self.scrollCalcTable.setWidget(self.scrollCalcTableContent)

        self.verticalLayout.addWidget(self.scrollCalcTable)


        self.vlCalc.addWidget(self.gbCalcTable)

        self.tabTemplateMode.addTab(self.tabCalcLimit, "")
        self.tabUT = QWidget()
        self.tabUT.setObjectName(u"tabUT")
        self.glUT = QGridLayout(self.tabUT)
        self.glUT.setObjectName(u"glUT")
        self.btnUTClear = QPushButton(self.tabUT)
        self.btnUTClear.setObjectName(u"btnUTClear")

        self.glUT.addWidget(self.btnUTClear, 0, 3, 1, 1)

        self.btnUTAddRow = QPushButton(self.tabUT)
        self.btnUTAddRow.setObjectName(u"btnUTAddRow")

        self.glUT.addWidget(self.btnUTAddRow, 0, 1, 1, 1)

        self.tblUTConfig = QTableWidget(self.tabUT)
        self.tblUTConfig.setObjectName(u"tblUTConfig")

        self.glUT.addWidget(self.tblUTConfig, 1, 0, 1, 4)

        self.btnUTPaste = QPushButton(self.tabUT)
        self.btnUTPaste.setObjectName(u"btnUTPaste")

        self.glUT.addWidget(self.btnUTPaste, 0, 0, 1, 1)

        self.btnUTDeleteRow = QPushButton(self.tabUT)
        self.btnUTDeleteRow.setObjectName(u"btnUTDeleteRow")

        self.glUT.addWidget(self.btnUTDeleteRow, 0, 2, 1, 1)

        self.tabTemplateMode.addTab(self.tabUT, "")

        self.vlTemplate.addWidget(self.tabTemplateMode)

        self.tabConfig.addTab(self.tabTemplate, "")
        self.tabPlot = QWidget()
        self.tabPlot.setObjectName(u"tabPlot")
        self.vlPlot = QVBoxLayout(self.tabPlot)
        self.vlPlot.setObjectName(u"vlPlot")
        self.scrollPlotConfig = QScrollArea(self.tabPlot)
        self.scrollPlotConfig.setObjectName(u"scrollPlotConfig")
        self.scrollPlotConfig.setWidgetResizable(True)
        self.scrollPlotConfigContent = QWidget()
        self.scrollPlotConfigContent.setObjectName(u"scrollPlotConfigContent")
        self.scrollPlotConfigContent.setGeometry(QRect(0, 0, 787, 830))
        self.gridLayout_5 = QGridLayout(self.scrollPlotConfigContent)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.verticalSpacer_6 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_5.addItem(self.verticalSpacer_6, 17, 1, 1, 1)

        self.gbXLabel = QFrame(self.scrollPlotConfigContent)
        self.gbXLabel.setObjectName(u"gbXLabel")
        self.gbXLabel.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbXLabel.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_3 = QHBoxLayout(self.gbXLabel)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.lblXLabel = QLabel(self.gbXLabel)
        self.lblXLabel.setObjectName(u"lblXLabel")

        self.horizontalLayout_3.addWidget(self.lblXLabel)

        self.horizontalSpacer_3 = QSpacerItem(189, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.editXLabel = QLineEdit(self.gbXLabel)
        self.editXLabel.setObjectName(u"editXLabel")

        self.horizontalLayout_3.addWidget(self.editXLabel)


        self.gridLayout_5.addWidget(self.gbXLabel, 1, 0, 1, 1)

        self.gbMarkerOpacity = QFrame(self.scrollPlotConfigContent)
        self.gbMarkerOpacity.setObjectName(u"gbMarkerOpacity")
        self.gbMarkerOpacity.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbMarkerOpacity.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_8 = QHBoxLayout(self.gbMarkerOpacity)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.lblMarkerOpacity = QLabel(self.gbMarkerOpacity)
        self.lblMarkerOpacity.setObjectName(u"lblMarkerOpacity")

        self.horizontalLayout_8.addWidget(self.lblMarkerOpacity)

        self.horizontalSpacer_8 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_8)

        self.spnMarkerOpacity = QSpinBox(self.gbMarkerOpacity)
        self.spnMarkerOpacity.setObjectName(u"spnMarkerOpacity")
        self.spnMarkerOpacity.setMinimum(0)
        self.spnMarkerOpacity.setMaximum(100)
        self.spnMarkerOpacity.setValue(75)

        self.horizontalLayout_8.addWidget(self.spnMarkerOpacity)


        self.gridLayout_5.addWidget(self.gbMarkerOpacity, 4, 0, 1, 1)

        self.gbPlotRows = QFrame(self.scrollPlotConfigContent)
        self.gbPlotRows.setObjectName(u"gbPlotRows")
        self.gbPlotRows.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbPlotRows.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_11 = QHBoxLayout(self.gbPlotRows)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.lblPlotRows = QLabel(self.gbPlotRows)
        self.lblPlotRows.setObjectName(u"lblPlotRows")

        self.horizontalLayout_11.addWidget(self.lblPlotRows)

        self.horizontalSpacer_11 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_11)

        self.spnPlotRows = QSpinBox(self.gbPlotRows)
        self.spnPlotRows.setObjectName(u"spnPlotRows")
        self.spnPlotRows.setMinimum(1)
        self.spnPlotRows.setMaximum(4)
        self.spnPlotRows.setValue(2)

        self.horizontalLayout_11.addWidget(self.spnPlotRows)


        self.gridLayout_5.addWidget(self.gbPlotRows, 5, 0, 1, 1)

        self.gbXRange = QFrame(self.scrollPlotConfigContent)
        self.gbXRange.setObjectName(u"gbXRange")
        self.gbXRange.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbXRange.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_13 = QHBoxLayout(self.gbXRange)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.lblXRange = QLabel(self.gbXRange)
        self.lblXRange.setObjectName(u"lblXRange")

        self.horizontalLayout_13.addWidget(self.lblXRange)

        self.horizontalSpacer_13 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_13)

        self.chkXAuto = QCheckBox(self.gbXRange)
        self.chkXAuto.setObjectName(u"chkXAuto")
        self.chkXAuto.setChecked(True)

        self.horizontalLayout_13.addWidget(self.chkXAuto)

        self.lblXMin = QLabel(self.gbXRange)
        self.lblXMin.setObjectName(u"lblXMin")

        self.horizontalLayout_13.addWidget(self.lblXMin)

        self.editXMin = QLineEdit(self.gbXRange)
        self.editXMin.setObjectName(u"editXMin")
        self.editXMin.setReadOnly(False)

        self.horizontalLayout_13.addWidget(self.editXMin)

        self.lblXMax = QLabel(self.gbXRange)
        self.lblXMax.setObjectName(u"lblXMax")

        self.horizontalLayout_13.addWidget(self.lblXMax)

        self.editXMax = QLineEdit(self.gbXRange)
        self.editXMax.setObjectName(u"editXMax")
        self.editXMax.setReadOnly(False)

        self.horizontalLayout_13.addWidget(self.editXMax)


        self.gridLayout_5.addWidget(self.gbXRange, 8, 0, 1, 1)

        self.gbLegendFontSize = QFrame(self.scrollPlotConfigContent)
        self.gbLegendFontSize.setObjectName(u"gbLegendFontSize")
        self.gbLegendFontSize.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbLegendFontSize.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_20 = QHBoxLayout(self.gbLegendFontSize)
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.lblLegendFontSize = QLabel(self.gbLegendFontSize)
        self.lblLegendFontSize.setObjectName(u"lblLegendFontSize")

        self.horizontalLayout_20.addWidget(self.lblLegendFontSize)

        self.horizontalSpacer_20 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_20.addItem(self.horizontalSpacer_20)

        self.spnLegendFontSize = QSpinBox(self.gbLegendFontSize)
        self.spnLegendFontSize.setObjectName(u"spnLegendFontSize")
        self.spnLegendFontSize.setMinimum(1)
        self.spnLegendFontSize.setMaximum(32)
        self.spnLegendFontSize.setValue(12)

        self.horizontalLayout_20.addWidget(self.spnLegendFontSize)


        self.gridLayout_5.addWidget(self.gbLegendFontSize, 11, 0, 1, 1)

        self.gbPlotCols = QFrame(self.scrollPlotConfigContent)
        self.gbPlotCols.setObjectName(u"gbPlotCols")
        self.gbPlotCols.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbPlotCols.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_10 = QHBoxLayout(self.gbPlotCols)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.lblPlotCols = QLabel(self.gbPlotCols)
        self.lblPlotCols.setObjectName(u"lblPlotCols")

        self.horizontalLayout_10.addWidget(self.lblPlotCols)

        self.horizontalSpacer_10 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_10)

        self.spnPlotCols = QSpinBox(self.gbPlotCols)
        self.spnPlotCols.setObjectName(u"spnPlotCols")
        self.spnPlotCols.setMinimum(1)
        self.spnPlotCols.setMaximum(4)
        self.spnPlotCols.setValue(2)

        self.horizontalLayout_10.addWidget(self.spnPlotCols)


        self.gridLayout_5.addWidget(self.gbPlotCols, 5, 1, 1, 1)

        self.gbTheme = QFrame(self.scrollPlotConfigContent)
        self.gbTheme.setObjectName(u"gbTheme")
        self.gbTheme.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbTheme.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_12 = QHBoxLayout(self.gbTheme)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.lblTheme = QLabel(self.gbTheme)
        self.lblTheme.setObjectName(u"lblTheme")

        self.horizontalLayout_12.addWidget(self.lblTheme)

        self.horizontalSpacer_12 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_12)

        self.cmbTheme = QComboBox(self.gbTheme)
        self.cmbTheme.addItem("")
        self.cmbTheme.addItem("")
        self.cmbTheme.addItem("")
        self.cmbTheme.addItem("")
        self.cmbTheme.addItem("")
        self.cmbTheme.addItem("")
        self.cmbTheme.addItem("")
        self.cmbTheme.setObjectName(u"cmbTheme")

        self.horizontalLayout_12.addWidget(self.cmbTheme)


        self.gridLayout_5.addWidget(self.gbTheme, 6, 0, 1, 1)

        self.gbGroupBy = QFrame(self.scrollPlotConfigContent)
        self.gbGroupBy.setObjectName(u"gbGroupBy")
        self.gbGroupBy.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbGroupBy.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_6 = QHBoxLayout(self.gbGroupBy)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.lblGroupBy = QLabel(self.gbGroupBy)
        self.lblGroupBy.setObjectName(u"lblGroupBy")

        self.horizontalLayout_6.addWidget(self.lblGroupBy)

        self.horizontalSpacer_6 = QSpacerItem(281, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_6)

        self.cmbGroupBy = QComboBox(self.gbGroupBy)
        self.cmbGroupBy.addItem("")
        self.cmbGroupBy.addItem("")
        self.cmbGroupBy.setObjectName(u"cmbGroupBy")

        self.horizontalLayout_6.addWidget(self.cmbGroupBy)


        self.gridLayout_5.addWidget(self.gbGroupBy, 2, 1, 1, 1)

        self.gbSaveDir = QFrame(self.scrollPlotConfigContent)
        self.gbSaveDir.setObjectName(u"gbSaveDir")
        self.gbSaveDir.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbSaveDir.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_17 = QHBoxLayout(self.gbSaveDir)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.lblSaveDir = QLabel(self.gbSaveDir)
        self.lblSaveDir.setObjectName(u"lblSaveDir")

        self.horizontalLayout_17.addWidget(self.lblSaveDir)

        self.horizontalSpacer_17 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_17)

        self.editSaveDir = QLineEdit(self.gbSaveDir)
        self.editSaveDir.setObjectName(u"editSaveDir")
        self.editSaveDir.setMinimumSize(QSize(240, 0))

        self.horizontalLayout_17.addWidget(self.editSaveDir)

        self.btnSelectSaveDir = QPushButton(self.gbSaveDir)
        self.btnSelectSaveDir.setObjectName(u"btnSelectSaveDir")

        self.horizontalLayout_17.addWidget(self.btnSelectSaveDir)


        self.gridLayout_5.addWidget(self.gbSaveDir, 9, 0, 1, 1)

        self.gbLineWidth = QFrame(self.scrollPlotConfigContent)
        self.gbLineWidth.setObjectName(u"gbLineWidth")
        self.gbLineWidth.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbLineWidth.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_7 = QHBoxLayout(self.gbLineWidth)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.lblLineWidth = QLabel(self.gbLineWidth)
        self.lblLineWidth.setObjectName(u"lblLineWidth")

        self.horizontalLayout_7.addWidget(self.lblLineWidth)

        self.spnLineWidth = QSpinBox(self.gbLineWidth)
        self.spnLineWidth.setObjectName(u"spnLineWidth")
        self.spnLineWidth.setMinimum(1)
        self.spnLineWidth.setMaximum(12)
        self.spnLineWidth.setValue(4)

        self.horizontalLayout_7.addWidget(self.spnLineWidth)

        self.horizontalSpacer_7 = QSpacerItem(0, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_7)

        self.lblLineframeWidth = QLabel(self.gbLineWidth)
        self.lblLineframeWidth.setObjectName(u"lblLineframeWidth")

        self.horizontalLayout_7.addWidget(self.lblLineframeWidth)

        self.spnLineframeWidth = QSpinBox(self.gbLineWidth)
        self.spnLineframeWidth.setObjectName(u"spnLineframeWidth")
        self.spnLineframeWidth.setMinimum(0)
        self.spnLineframeWidth.setMaximum(12)
        self.spnLineframeWidth.setValue(1)

        self.horizontalLayout_7.addWidget(self.spnLineframeWidth)


        self.gridLayout_5.addWidget(self.gbLineWidth, 3, 1, 1, 1)

        self.gbPlotSize = QFrame(self.scrollPlotConfigContent)
        self.gbPlotSize.setObjectName(u"gbPlotSize")
        self.gbPlotSize.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbPlotSize.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_15 = QHBoxLayout(self.gbPlotSize)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.lblPlotSize = QLabel(self.gbPlotSize)
        self.lblPlotSize.setObjectName(u"lblPlotSize")

        self.horizontalLayout_15.addWidget(self.lblPlotSize)

        self.horizontalSpacer_15 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_15.addItem(self.horizontalSpacer_15)

        self.lblWidth = QLabel(self.gbPlotSize)
        self.lblWidth.setObjectName(u"lblWidth")

        self.horizontalLayout_15.addWidget(self.lblWidth)

        self.spnWidth = QSpinBox(self.gbPlotSize)
        self.spnWidth.setObjectName(u"spnWidth")
        self.spnWidth.setMinimum(0)
        self.spnWidth.setMaximum(3600)
        self.spnWidth.setValue(600)

        self.horizontalLayout_15.addWidget(self.spnWidth)

        self.lblHeight = QLabel(self.gbPlotSize)
        self.lblHeight.setObjectName(u"lblHeight")

        self.horizontalLayout_15.addWidget(self.lblHeight)

        self.spnHeight = QSpinBox(self.gbPlotSize)
        self.spnHeight.setObjectName(u"spnHeight")
        self.spnHeight.setMinimum(0)
        self.spnHeight.setMaximum(3600)
        self.spnHeight.setValue(400)

        self.horizontalLayout_15.addWidget(self.spnHeight)


        self.gridLayout_5.addWidget(self.gbPlotSize, 6, 1, 1, 1)

        self.gbPlotType = QFrame(self.scrollPlotConfigContent)
        self.gbPlotType.setObjectName(u"gbPlotType")
        self.gbPlotType.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbPlotType.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_5 = QHBoxLayout(self.gbPlotType)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.lblPlotType = QLabel(self.gbPlotType)
        self.lblPlotType.setObjectName(u"lblPlotType")

        self.horizontalLayout_5.addWidget(self.lblPlotType)

        self.horizontalSpacer_5 = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_5)

        self.cmbPlotType = QComboBox(self.gbPlotType)
        self.cmbPlotType.addItem("")
        self.cmbPlotType.addItem("")
        self.cmbPlotType.addItem("")
        self.cmbPlotType.setObjectName(u"cmbPlotType")

        self.horizontalLayout_5.addWidget(self.cmbPlotType)


        self.gridLayout_5.addWidget(self.gbPlotType, 2, 0, 1, 1)

        self.gbYAxisData = QFrame(self.scrollPlotConfigContent)
        self.gbYAxisData.setObjectName(u"gbYAxisData")
        self.gbYAxisData.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbYAxisData.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_4 = QHBoxLayout(self.gbYAxisData)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.lblYAxisData = QLabel(self.gbYAxisData)
        self.lblYAxisData.setObjectName(u"lblYAxisData")

        self.horizontalLayout_4.addWidget(self.lblYAxisData)

        self.horizontalSpacer_4 = QSpacerItem(215, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)

        self.cmbYAxisData = QComboBox(self.gbYAxisData)
        self.cmbYAxisData.addItem("")
        self.cmbYAxisData.addItem("")
        self.cmbYAxisData.setObjectName(u"cmbYAxisData")

        self.horizontalLayout_4.addWidget(self.cmbYAxisData)


        self.gridLayout_5.addWidget(self.gbYAxisData, 1, 1, 1, 1)

        self.gbDrawData = QFrame(self.scrollPlotConfigContent)
        self.gbDrawData.setObjectName(u"gbDrawData")
        self.gbDrawData.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbDrawData.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout = QHBoxLayout(self.gbDrawData)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lblDrawData = QLabel(self.gbDrawData)
        self.lblDrawData.setObjectName(u"lblDrawData")

        self.horizontalLayout.addWidget(self.lblDrawData)

        self.horizontalSpacer = QSpacerItem(137, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.chkDrawT0 = QCheckBox(self.gbDrawData)
        self.chkDrawT0.setObjectName(u"chkDrawT0")

        self.horizontalLayout.addWidget(self.chkDrawT0)

        self.chkDrawTx = QCheckBox(self.gbDrawData)
        self.chkDrawTx.setObjectName(u"chkDrawTx")

        self.horizontalLayout.addWidget(self.chkDrawTx)

        self.chkDrawShift = QCheckBox(self.gbDrawData)
        self.chkDrawShift.setObjectName(u"chkDrawShift")
        self.chkDrawShift.setChecked(True)

        self.horizontalLayout.addWidget(self.chkDrawShift)


        self.gridLayout_5.addWidget(self.gbDrawData, 0, 0, 1, 1)

        self.gbHover = QFrame(self.scrollPlotConfigContent)
        self.gbHover.setObjectName(u"gbHover")
        self.gbHover.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbHover.setFrameShadow(QFrame.Shadow.Sunken)
        self.gridLayout_6 = QGridLayout(self.gbHover)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.lblHover = QLabel(self.gbHover)
        self.lblHover.setObjectName(u"lblHover")

        self.gridLayout_6.addWidget(self.lblHover, 0, 0, 1, 1)

        self.horizontalSpacer_24 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_6.addItem(self.horizontalSpacer_24, 0, 1, 1, 1)

        self.btnHoverHelp = QPushButton(self.gbHover)
        self.btnHoverHelp.setObjectName(u"btnHoverHelp")

        self.gridLayout_6.addWidget(self.btnHoverHelp, 1, 0, 1, 1)

        self.editHoverTemplate = QPlainTextEdit(self.gbHover)
        self.editHoverTemplate.setObjectName(u"editHoverTemplate")

        self.gridLayout_6.addWidget(self.editHoverTemplate, 0, 2, 2, 1)


        self.gridLayout_5.addWidget(self.gbHover, 15, 0, 3, 1)

        self.gbTickDecimals = QFrame(self.scrollPlotConfigContent)
        self.gbTickDecimals.setObjectName(u"gbTickDecimals")
        self.gbTickDecimals.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbTickDecimals.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_22 = QHBoxLayout(self.gbTickDecimals)
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.lblTickDecimals = QLabel(self.gbTickDecimals)
        self.lblTickDecimals.setObjectName(u"lblTickDecimals")

        self.horizontalLayout_22.addWidget(self.lblTickDecimals)

        self.horizontalSpacer_22 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_22.addItem(self.horizontalSpacer_22)

        self.spnTickDecimals = QSpinBox(self.gbTickDecimals)
        self.spnTickDecimals.setObjectName(u"spnTickDecimals")
        self.spnTickDecimals.setMinimum(0)
        self.spnTickDecimals.setMaximum(8)
        self.spnTickDecimals.setValue(2)

        self.horizontalLayout_22.addWidget(self.spnTickDecimals)


        self.gridLayout_5.addWidget(self.gbTickDecimals, 15, 1, 1, 1)

        self.gbLabelFontSize = QFrame(self.scrollPlotConfigContent)
        self.gbLabelFontSize.setObjectName(u"gbLabelFontSize")
        self.gbLabelFontSize.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbLabelFontSize.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_19 = QHBoxLayout(self.gbLabelFontSize)
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.lblLabelFontSize = QLabel(self.gbLabelFontSize)
        self.lblLabelFontSize.setObjectName(u"lblLabelFontSize")

        self.horizontalLayout_19.addWidget(self.lblLabelFontSize)

        self.horizontalSpacer_19 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_19.addItem(self.horizontalSpacer_19)

        self.spnLabelFontSize = QSpinBox(self.gbLabelFontSize)
        self.spnLabelFontSize.setObjectName(u"spnLabelFontSize")
        self.spnLabelFontSize.setMinimum(1)
        self.spnLabelFontSize.setMaximum(32)
        self.spnLabelFontSize.setValue(12)

        self.horizontalLayout_19.addWidget(self.spnLabelFontSize)


        self.gridLayout_5.addWidget(self.gbLabelFontSize, 10, 1, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 9, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_5.addItem(self.verticalSpacer_4, 18, 1, 1, 1)

        self.verticalSpacer_5 = QSpacerItem(20, 9, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_5.addItem(self.verticalSpacer_5, 18, 0, 1, 1)

        self.gbHoverFontSize = QFrame(self.scrollPlotConfigContent)
        self.gbHoverFontSize.setObjectName(u"gbHoverFontSize")
        self.gbHoverFontSize.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbHoverFontSize.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_23 = QHBoxLayout(self.gbHoverFontSize)
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.lblHoverFontSize = QLabel(self.gbHoverFontSize)
        self.lblHoverFontSize.setObjectName(u"lblHoverFontSize")

        self.horizontalLayout_23.addWidget(self.lblHoverFontSize)

        self.horizontalSpacer_23 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_23.addItem(self.horizontalSpacer_23)

        self.spnHoverFontSize = QSpinBox(self.gbHoverFontSize)
        self.spnHoverFontSize.setObjectName(u"spnHoverFontSize")
        self.spnHoverFontSize.setMinimum(1)
        self.spnHoverFontSize.setMaximum(32)
        self.spnHoverFontSize.setValue(10)

        self.horizontalLayout_23.addWidget(self.spnHoverFontSize)


        self.gridLayout_5.addWidget(self.gbHoverFontSize, 11, 1, 1, 1)

        self.gbDataSource = QFrame(self.scrollPlotConfigContent)
        self.gbDataSource.setObjectName(u"gbDataSource")
        self.gbDataSource.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbDataSource.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_2 = QHBoxLayout(self.gbDataSource)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lblDataSource = QLabel(self.gbDataSource)
        self.lblDataSource.setObjectName(u"lblDataSource")

        self.horizontalLayout_2.addWidget(self.lblDataSource)

        self.horizontalSpacer_2 = QSpacerItem(173, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.rdoDataRaw = QRadioButton(self.gbDataSource)
        self.rdoDataRaw.setObjectName(u"rdoDataRaw")

        self.horizontalLayout_2.addWidget(self.rdoDataRaw)

        self.rdoDataMerged = QRadioButton(self.gbDataSource)
        self.rdoDataMerged.setObjectName(u"rdoDataMerged")
        self.rdoDataMerged.setChecked(True)

        self.horizontalLayout_2.addWidget(self.rdoDataMerged)


        self.gridLayout_5.addWidget(self.gbDataSource, 0, 1, 1, 1)

        self.gbLineOpacity = QFrame(self.scrollPlotConfigContent)
        self.gbLineOpacity.setObjectName(u"gbLineOpacity")
        self.gbLineOpacity.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbLineOpacity.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_9 = QHBoxLayout(self.gbLineOpacity)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.lblLineOpacity = QLabel(self.gbLineOpacity)
        self.lblLineOpacity.setObjectName(u"lblLineOpacity")

        self.horizontalLayout_9.addWidget(self.lblLineOpacity)

        self.horizontalSpacer_9 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_9)

        self.spnLineOpacity = QSpinBox(self.gbLineOpacity)
        self.spnLineOpacity.setObjectName(u"spnLineOpacity")
        self.spnLineOpacity.setMinimum(0)
        self.spnLineOpacity.setMaximum(100)
        self.spnLineOpacity.setValue(75)

        self.horizontalLayout_9.addWidget(self.spnLineOpacity)


        self.gridLayout_5.addWidget(self.gbLineOpacity, 4, 1, 1, 1)

        self.gbTickFormat = QFrame(self.scrollPlotConfigContent)
        self.gbTickFormat.setObjectName(u"gbTickFormat")
        self.gbTickFormat.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbTickFormat.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_21 = QHBoxLayout(self.gbTickFormat)
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.lblTickFormat = QLabel(self.gbTickFormat)
        self.lblTickFormat.setObjectName(u"lblTickFormat")

        self.horizontalLayout_21.addWidget(self.lblTickFormat)

        self.horizontalSpacer_21 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_21.addItem(self.horizontalSpacer_21)

        self.cmbTickFormat = QComboBox(self.gbTickFormat)
        self.cmbTickFormat.addItem("")
        self.cmbTickFormat.addItem("")
        self.cmbTickFormat.setObjectName(u"cmbTickFormat")

        self.horizontalLayout_21.addWidget(self.cmbTickFormat)


        self.gridLayout_5.addWidget(self.gbTickFormat, 13, 1, 1, 1)

        self.gbOutputFormat = QFrame(self.scrollPlotConfigContent)
        self.gbOutputFormat.setObjectName(u"gbOutputFormat")
        self.gbOutputFormat.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbOutputFormat.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_16 = QHBoxLayout(self.gbOutputFormat)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.lblOutputFormat = QLabel(self.gbOutputFormat)
        self.lblOutputFormat.setObjectName(u"lblOutputFormat")

        self.horizontalLayout_16.addWidget(self.lblOutputFormat)

        self.horizontalSpacer_16 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_16)

        self.cmbOutputFormat = QComboBox(self.gbOutputFormat)
        self.cmbOutputFormat.addItem("")
        self.cmbOutputFormat.addItem("")
        self.cmbOutputFormat.addItem("")
        self.cmbOutputFormat.addItem("")
        self.cmbOutputFormat.addItem("")
        self.cmbOutputFormat.addItem("")
        self.cmbOutputFormat.setObjectName(u"cmbOutputFormat")

        self.horizontalLayout_16.addWidget(self.cmbOutputFormat)


        self.gridLayout_5.addWidget(self.gbOutputFormat, 9, 1, 1, 1)

        self.gbTickFormat_4 = QFrame(self.scrollPlotConfigContent)
        self.gbTickFormat_4.setObjectName(u"gbTickFormat_4")
        self.gbTickFormat_4.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbTickFormat_4.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_27 = QHBoxLayout(self.gbTickFormat_4)
        self.horizontalLayout_27.setObjectName(u"horizontalLayout_27")
        self.lblYscale = QLabel(self.gbTickFormat_4)
        self.lblYscale.setObjectName(u"lblYscale")

        self.horizontalLayout_27.addWidget(self.lblYscale)

        self.horizontalSpacer_29 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_27.addItem(self.horizontalSpacer_29)

        self.cmbYScale = QComboBox(self.gbTickFormat_4)
        self.cmbYScale.addItem("")
        self.cmbYScale.addItem("")
        self.cmbYScale.setObjectName(u"cmbYScale")

        self.horizontalLayout_27.addWidget(self.cmbYScale)


        self.gridLayout_5.addWidget(self.gbTickFormat_4, 7, 1, 1, 1)

        self.gbYRange = QFrame(self.scrollPlotConfigContent)
        self.gbYRange.setObjectName(u"gbYRange")
        self.gbYRange.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbYRange.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_14 = QHBoxLayout(self.gbYRange)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.lblYRange = QLabel(self.gbYRange)
        self.lblYRange.setObjectName(u"lblYRange")

        self.horizontalLayout_14.addWidget(self.lblYRange)

        self.horizontalSpacer_14 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_14.addItem(self.horizontalSpacer_14)

        self.chkYAuto = QCheckBox(self.gbYRange)
        self.chkYAuto.setObjectName(u"chkYAuto")
        self.chkYAuto.setChecked(True)

        self.horizontalLayout_14.addWidget(self.chkYAuto)

        self.lblYMin = QLabel(self.gbYRange)
        self.lblYMin.setObjectName(u"lblYMin")

        self.horizontalLayout_14.addWidget(self.lblYMin)

        self.editYMin = QLineEdit(self.gbYRange)
        self.editYMin.setObjectName(u"editYMin")
        self.editYMin.setReadOnly(False)

        self.horizontalLayout_14.addWidget(self.editYMin)

        self.lblYMax = QLabel(self.gbYRange)
        self.lblYMax.setObjectName(u"lblYMax")

        self.horizontalLayout_14.addWidget(self.lblYMax)

        self.editYMax = QLineEdit(self.gbYRange)
        self.editYMax.setObjectName(u"editYMax")
        self.editYMax.setReadOnly(False)

        self.horizontalLayout_14.addWidget(self.editYMax)


        self.gridLayout_5.addWidget(self.gbYRange, 8, 1, 1, 1)

        self.gbMarkerSize = QFrame(self.scrollPlotConfigContent)
        self.gbMarkerSize.setObjectName(u"gbMarkerSize")
        self.gbMarkerSize.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbMarkerSize.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_28 = QHBoxLayout(self.gbMarkerSize)
        self.horizontalLayout_28.setObjectName(u"horizontalLayout_28")
        self.lblMarkerSize = QLabel(self.gbMarkerSize)
        self.lblMarkerSize.setObjectName(u"lblMarkerSize")

        self.horizontalLayout_28.addWidget(self.lblMarkerSize)

        self.spnMarkerSize = QSpinBox(self.gbMarkerSize)
        self.spnMarkerSize.setObjectName(u"spnMarkerSize")
        self.spnMarkerSize.setMinimum(1)
        self.spnMarkerSize.setMaximum(12)
        self.spnMarkerSize.setValue(6)

        self.horizontalLayout_28.addWidget(self.spnMarkerSize)

        self.horizontalSpacer_28 = QSpacerItem(333, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_28.addItem(self.horizontalSpacer_28)

        self.lblMarkerframeSize = QLabel(self.gbMarkerSize)
        self.lblMarkerframeSize.setObjectName(u"lblMarkerframeSize")

        self.horizontalLayout_28.addWidget(self.lblMarkerframeSize)

        self.spnMarkerframeSize = QSpinBox(self.gbMarkerSize)
        self.spnMarkerframeSize.setObjectName(u"spnMarkerframeSize")
        self.spnMarkerframeSize.setMinimum(0)
        self.spnMarkerframeSize.setMaximum(12)
        self.spnMarkerframeSize.setValue(1)

        self.horizontalLayout_28.addWidget(self.spnMarkerframeSize)


        self.gridLayout_5.addWidget(self.gbMarkerSize, 3, 0, 1, 1)

        self.gbTickFormat_3 = QFrame(self.scrollPlotConfigContent)
        self.gbTickFormat_3.setObjectName(u"gbTickFormat_3")
        self.gbTickFormat_3.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbTickFormat_3.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_26 = QHBoxLayout(self.gbTickFormat_3)
        self.horizontalLayout_26.setObjectName(u"horizontalLayout_26")
        self.lblXScale = QLabel(self.gbTickFormat_3)
        self.lblXScale.setObjectName(u"lblXScale")

        self.horizontalLayout_26.addWidget(self.lblXScale)

        self.horizontalSpacer_27 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_26.addItem(self.horizontalSpacer_27)

        self.cmbXScale = QComboBox(self.gbTickFormat_3)
        self.cmbXScale.addItem("")
        self.cmbXScale.addItem("")
        self.cmbXScale.setObjectName(u"cmbXScale")

        self.horizontalLayout_26.addWidget(self.cmbXScale)


        self.gridLayout_5.addWidget(self.gbTickFormat_3, 7, 0, 1, 1)

        self.gbLimitDisplay = QFrame(self.scrollPlotConfigContent)
        self.gbLimitDisplay.setObjectName(u"gbLimitDisplay")
        self.gbLimitDisplay.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbLimitDisplay.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_25 = QHBoxLayout(self.gbLimitDisplay)
        self.horizontalLayout_25.setObjectName(u"horizontalLayout_25")
        self.lblLimit = QLabel(self.gbLimitDisplay)
        self.lblLimit.setObjectName(u"lblLimit")

        self.horizontalLayout_25.addWidget(self.lblLimit)

        self.horizontalSpacer_25 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_25.addItem(self.horizontalSpacer_25)

        self.chkShowLimitLine = QCheckBox(self.gbLimitDisplay)
        self.chkShowLimitLine.setObjectName(u"chkShowLimitLine")
        self.chkShowLimitLine.setChecked(True)

        self.horizontalLayout_25.addWidget(self.chkShowLimitLine)

        self.chkDrawOverLimit = QCheckBox(self.gbLimitDisplay)
        self.chkDrawOverLimit.setObjectName(u"chkDrawOverLimit")
        self.chkDrawOverLimit.setChecked(True)

        self.horizontalLayout_25.addWidget(self.chkDrawOverLimit)


        self.gridLayout_5.addWidget(self.gbLimitDisplay, 13, 0, 1, 1)

        self.gbTitleFontSize = QFrame(self.scrollPlotConfigContent)
        self.gbTitleFontSize.setObjectName(u"gbTitleFontSize")
        self.gbTitleFontSize.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbTitleFontSize.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_18 = QHBoxLayout(self.gbTitleFontSize)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.lblTitleFontSize = QLabel(self.gbTitleFontSize)
        self.lblTitleFontSize.setObjectName(u"lblTitleFontSize")

        self.horizontalLayout_18.addWidget(self.lblTitleFontSize)

        self.horizontalSpacer_18 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_18.addItem(self.horizontalSpacer_18)

        self.spnTitleFontSize = QSpinBox(self.gbTitleFontSize)
        self.spnTitleFontSize.setObjectName(u"spnTitleFontSize")
        self.spnTitleFontSize.setMinimum(1)
        self.spnTitleFontSize.setMaximum(32)
        self.spnTitleFontSize.setValue(18)

        self.horizontalLayout_18.addWidget(self.spnTitleFontSize)


        self.gridLayout_5.addWidget(self.gbTitleFontSize, 10, 0, 1, 1)

        self.gbTickDecimals_2 = QFrame(self.scrollPlotConfigContent)
        self.gbTickDecimals_2.setObjectName(u"gbTickDecimals_2")
        self.gbTickDecimals_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.gbTickDecimals_2.setFrameShadow(QFrame.Shadow.Sunken)
        self.horizontalLayout_24 = QHBoxLayout(self.gbTickDecimals_2)
        self.horizontalLayout_24.setObjectName(u"horizontalLayout_24")
        self.lblWebengineScale = QLabel(self.gbTickDecimals_2)
        self.lblWebengineScale.setObjectName(u"lblWebengineScale")

        self.horizontalLayout_24.addWidget(self.lblWebengineScale)

        self.horizontalSpacer_26 = QSpacerItem(213, 24, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_24.addItem(self.horizontalSpacer_26)

        self.spnWebengineScale = QSpinBox(self.gbTickDecimals_2)
        self.spnWebengineScale.setObjectName(u"spnWebengineScale")
        self.spnWebengineScale.setMinimum(10)
        self.spnWebengineScale.setMaximum(1000)
        self.spnWebengineScale.setSingleStep(10)
        self.spnWebengineScale.setValue(100)

        self.horizontalLayout_24.addWidget(self.spnWebengineScale)


        self.gridLayout_5.addWidget(self.gbTickDecimals_2, 16, 1, 1, 1)

        self.scrollPlotConfig.setWidget(self.scrollPlotConfigContent)

        self.vlPlot.addWidget(self.scrollPlotConfig)

        self.tabConfig.addTab(self.tabPlot, "")

        self.gridLayout.addWidget(self.tabConfig, 1, 0, 1, 1)

        self.frameButtons = QFrame(ConfigDialog)
        self.frameButtons.setObjectName(u"frameButtons")
        self.frameButtons.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameButtons.setFrameShadow(QFrame.Shadow.Raised)
        self.hlButtons = QHBoxLayout(self.frameButtons)
        self.hlButtons.setObjectName(u"hlButtons")
        self.btnReadFTData = QPushButton(self.frameButtons)
        self.btnReadFTData.setObjectName(u"btnReadFTData")

        self.hlButtons.addWidget(self.btnReadFTData)

        self.spacerButtonsLeft = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlButtons.addItem(self.spacerButtonsLeft)

        self.btnOK = QPushButton(self.frameButtons)
        self.btnOK.setObjectName(u"btnOK")

        self.hlButtons.addWidget(self.btnOK)

        self.btnCancel = QPushButton(self.frameButtons)
        self.btnCancel.setObjectName(u"btnCancel")

        self.hlButtons.addWidget(self.btnCancel)


        self.gridLayout.addWidget(self.frameButtons, 2, 0, 1, 1)


        self.retranslateUi(ConfigDialog)

        self.tabConfig.setCurrentIndex(1)
        self.tabGroupMode.setCurrentIndex(0)
        self.tabTemplateMode.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ConfigDialog)
    # setupUi

    def retranslateUi(self, ConfigDialog):
        ConfigDialog.setWindowTitle(QCoreApplication.translate("ConfigDialog", u"\u914d\u7f6e", None))
        self.gbConfigSelect.setTitle(QCoreApplication.translate("ConfigDialog", u"\u914d\u7f6e\u9879\u9009\u62e9", None))
        self.btnConfigFileSelect.setText(QCoreApplication.translate("ConfigDialog", u"\u9009\u62e9\u914d\u7f6e\u6587\u4ef6", None))
        self.lblAddConfig.setText(QCoreApplication.translate("ConfigDialog", u"\u6dfb\u52a0\u914d\u7f6e\uff1a", None))
        self.btnAddConfig.setText(QCoreApplication.translate("ConfigDialog", u"\u6dfb\u52a0", None))
        self.lblConfig.setText(QCoreApplication.translate("ConfigDialog", u"\u914d\u7f6e\uff1a", None))
        self.lblCurrentConfigFile.setText(QCoreApplication.translate("ConfigDialog", u"\u5f53\u524d\u914d\u7f6e\u6587\u4ef6\uff1a", None))
        self.tabGroupMode.setTabText(self.tabGroupMode.indexOf(self.tabByName), QCoreApplication.translate("ConfigDialog", u"\u6309\u6587\u4ef6\u540d\u5206\u7ec4", None))
        self.btnClearSN.setText(QCoreApplication.translate("ConfigDialog", u"\u6e05\u9664\u5185\u5bb9", None))
        self.btnPasteSN.setText(QCoreApplication.translate("ConfigDialog", u"\u5bfc\u5165\u526a\u5207\u677f", None))
        self.tabGroupMode.setTabText(self.tabGroupMode.indexOf(self.tabBySN), QCoreApplication.translate("ConfigDialog", u"\u6309SN\u5206\u7ec4", None))
        self.gbGroupMode.setTitle(QCoreApplication.translate("ConfigDialog", u"\u5206\u7ec4\u65b9\u5f0f", None))
        self.rbByName.setText(QCoreApplication.translate("ConfigDialog", u"\u6309\u6587\u4ef6\u540d\u5206\u7ec4", None))
        self.rbBySN.setText(QCoreApplication.translate("ConfigDialog", u"\u6309SN\u5206\u7ec4", None))
        self.rbBoth.setText(QCoreApplication.translate("ConfigDialog", u"\u4e8c\u8005\u7ed3\u5408", None))
        self.tabConfig.setTabText(self.tabConfig.indexOf(self.tabGroup), QCoreApplication.translate("ConfigDialog", u"\u5206\u7ec4\u914d\u7f6e", None))
        self.lblCachePath.setText(QCoreApplication.translate("ConfigDialog", u"\u7f13\u5b58\u5730\u5740\uff1a", None))
        self.btnSelectTemplate.setText(QCoreApplication.translate("ConfigDialog", u"\u9009\u62e9", None))
        self.gbPreview.setTitle(QCoreApplication.translate("ConfigDialog", u"\u9884\u89c8", None))
        self.btnOpenCachePath.setText(QCoreApplication.translate("ConfigDialog", u"\u6253\u5f00", None))
        self.lblTemplatePath.setText(QCoreApplication.translate("ConfigDialog", u"\u6a21\u677f\u5730\u5740\uff1a", None))
        self.btnSelectCachePath.setText(QCoreApplication.translate("ConfigDialog", u"\u9009\u62e9", None))
        self.btnOpenTemplate.setText(QCoreApplication.translate("ConfigDialog", u"\u6253\u5f00", None))
        self.editCachePath.setText(QCoreApplication.translate("ConfigDialog", u"%PROGRAM_DIR%/cache", None))
        self.tabTemplateMode.setTabText(self.tabTemplateMode.indexOf(self.tabTemplateFile), QCoreApplication.translate("ConfigDialog", u"\u6a21\u677f\u6587\u4ef6\u914d\u7f6e", None))
        self.gbFilter.setTitle(QCoreApplication.translate("ConfigDialog", u"\u7b5b\u9009\u9879\u76ee", None))
        self.lblInclude.setText(QCoreApplication.translate("ConfigDialog", u"\u5305\u542b\u6587\u672c\uff1a", None))
        self.lblExclude.setText(QCoreApplication.translate("ConfigDialog", u"\u6392\u9664\u6587\u672c\uff1a", None))
        self.gbOrigin.setTitle(QCoreApplication.translate("ConfigDialog", u"\u539f\u59cb\u9879\u76ee", None))
        self.gbCandidate.setTitle(QCoreApplication.translate("ConfigDialog", u"\u5019\u9009\u9879\u76ee", None))
        self.btnMoveRight.setText(QCoreApplication.translate("ConfigDialog", u">", None))
        self.btnMoveLeft.setText(QCoreApplication.translate("ConfigDialog", u"<", None))
        self.btnMoveAllRight.setText(QCoreApplication.translate("ConfigDialog", u">>", None))
        self.btnMoveAllLeft.setText(QCoreApplication.translate("ConfigDialog", u"<<", None))
        self.gbSelected.setTitle(QCoreApplication.translate("ConfigDialog", u"\u5df2\u9009\u62e9\u9879\u76ee", None))
        self.tabTemplateMode.setTabText(self.tabTemplateMode.indexOf(self.tabTestItems), QCoreApplication.translate("ConfigDialog", u"\u6d4b\u8bd5\u9879\u914d\u7f6e", None))
        self.gbCalcFilter.setTitle(QCoreApplication.translate("ConfigDialog", u"\u7b5b\u9009", None))
        self.lblCalcInclude.setText(QCoreApplication.translate("ConfigDialog", u"\u5305\u542b\uff1a", None))
        self.lblCalcExclude.setText(QCoreApplication.translate("ConfigDialog", u"\u6392\u9664\uff1a", None))
        self.gbCalcBatch.setTitle(QCoreApplication.translate("ConfigDialog", u"\u6279\u91cf\u5e94\u7528", None))
        self.btnCalcApply.setText(QCoreApplication.translate("ConfigDialog", u"\u5e94\u7528", None))
        self.lblCalcRename.setText(QCoreApplication.translate("ConfigDialog", u"\u91cd\u547d\u540d\u4e3a\uff1a", None))
        self.lblCalcPreset.setText(QCoreApplication.translate("ConfigDialog", u"\u8ba1\u7b97\u516c\u5f0f\uff1a", None))
        self.lblCalcRenameSuffix.setText(QCoreApplication.translate("ConfigDialog", u"\u91cd\u547d\u540did\u540e\u7f00\uff1a", None))
        self.cmbCalcPreset.setItemText(0, QCoreApplication.translate("ConfigDialog", u"abs(T0/TX)", None))
        self.cmbCalcPreset.setItemText(1, QCoreApplication.translate("ConfigDialog", u"abs(1/((TX/T0)-1))", None))
        self.cmbCalcPreset.setItemText(2, QCoreApplication.translate("ConfigDialog", u"\u81ea\u5b9a\u4e49", None))

        self.cmbCalcLimitDir.setItemText(0, QCoreApplication.translate("ConfigDialog", u"lower", None))
        self.cmbCalcLimitDir.setItemText(1, QCoreApplication.translate("ConfigDialog", u"upper", None))

        self.lblCalcLimit.setText(QCoreApplication.translate("ConfigDialog", u"limit\uff1a", None))
        self.lblCalcLimitDir.setText(QCoreApplication.translate("ConfigDialog", u"limit side\uff1a", None))
        self.btnFormulaManage.setText(QCoreApplication.translate("ConfigDialog", u"\u7ba1\u7406\u516c\u5f0f", None))
        self.gbCalcTable.setTitle(QCoreApplication.translate("ConfigDialog", u"\u914d\u7f6e\u5185\u5bb9", None))
        self.tabTemplateMode.setTabText(self.tabTemplateMode.indexOf(self.tabCalcLimit), QCoreApplication.translate("ConfigDialog", u"\u6570\u636e\u8ba1\u7b97/limit\u914d\u7f6e", None))
        self.btnUTClear.setText(QCoreApplication.translate("ConfigDialog", u"\u6e05\u7a7a", None))
        self.btnUTAddRow.setText(QCoreApplication.translate("ConfigDialog", u"\u6dfb\u52a0\u884c", None))
        self.btnUTPaste.setText(QCoreApplication.translate("ConfigDialog", u"\u8bfb\u53d6\u526a\u5207\u677f", None))
        self.btnUTDeleteRow.setText(QCoreApplication.translate("ConfigDialog", u"\u5220\u9664\u9009\u4e2d\u884c", None))
        self.tabTemplateMode.setTabText(self.tabTemplateMode.indexOf(self.tabUT), QCoreApplication.translate("ConfigDialog", u"UT\u914d\u7f6e", None))
        self.tabConfig.setTabText(self.tabConfig.indexOf(self.tabTemplate), QCoreApplication.translate("ConfigDialog", u"\u6a21\u677f\u914d\u7f6e", None))
        self.lblXLabel.setText(QCoreApplication.translate("ConfigDialog", u"X\u8f74label\uff1a", None))
        self.editXLabel.setText(QCoreApplication.translate("ConfigDialog", u"shift \u8ba1\u7b97\u516c\u5f0f\uff1a %formula%", None))
        self.lblMarkerOpacity.setText(QCoreApplication.translate("ConfigDialog", u"marker\u900f\u660e\u5ea6", None))
        self.lblPlotRows.setText(QCoreApplication.translate("ConfigDialog", u"\u6bcf\u9875\u56fe\u8868\u884c\u6570", None))
        self.lblXRange.setText(QCoreApplication.translate("ConfigDialog", u"x\u8303\u56f4", None))
        self.chkXAuto.setText(QCoreApplication.translate("ConfigDialog", u"\u81ea\u52a8", None))
        self.lblXMin.setText(QCoreApplication.translate("ConfigDialog", u"min:", None))
        self.lblXMax.setText(QCoreApplication.translate("ConfigDialog", u"max:", None))
        self.lblLegendFontSize.setText(QCoreApplication.translate("ConfigDialog", u"\u56fe\u4f8b\u5b57\u53f7", None))
        self.lblPlotCols.setText(QCoreApplication.translate("ConfigDialog", u"\u6bcf\u9875\u56fe\u8868\u5217\u6570", None))
        self.lblTheme.setText(QCoreApplication.translate("ConfigDialog", u"\u4e3b\u9898", None))
        self.cmbTheme.setItemText(0, QCoreApplication.translate("ConfigDialog", u"plotly", None))
        self.cmbTheme.setItemText(1, QCoreApplication.translate("ConfigDialog", u"ggplot2", None))
        self.cmbTheme.setItemText(2, QCoreApplication.translate("ConfigDialog", u"seaborn", None))
        self.cmbTheme.setItemText(3, QCoreApplication.translate("ConfigDialog", u"presentation", None))
        self.cmbTheme.setItemText(4, QCoreApplication.translate("ConfigDialog", u"simple_white", None))
        self.cmbTheme.setItemText(5, QCoreApplication.translate("ConfigDialog", u"plotly_white", None))
        self.cmbTheme.setItemText(6, QCoreApplication.translate("ConfigDialog", u"plotly_dark", None))

        self.lblGroupBy.setText(QCoreApplication.translate("ConfigDialog", u"\u5206\u7ec4\u65b9\u5f0f", None))
        self.cmbGroupBy.setItemText(0, QCoreApplication.translate("ConfigDialog", u"group", None))
        self.cmbGroupBy.setItemText(1, QCoreApplication.translate("ConfigDialog", u"\u6d4b\u8bd5\u9879", None))

        self.lblSaveDir.setText(QCoreApplication.translate("ConfigDialog", u"\u4e34\u65f6\u4fdd\u5b58\u5730\u5740", None))
        self.editSaveDir.setText(QCoreApplication.translate("ConfigDialog", u"%DIR_TO_PROGRAM%/images", None))
        self.btnSelectSaveDir.setText(QCoreApplication.translate("ConfigDialog", u"\u9009\u62e9", None))
        self.lblLineWidth.setText(QCoreApplication.translate("ConfigDialog", u"\u7ebf\u5bbd", None))
        self.lblLineframeWidth.setText(QCoreApplication.translate("ConfigDialog", u"\u7ebf\u8fb9\u6846\u5bbd", None))
        self.lblPlotSize.setText(QCoreApplication.translate("ConfigDialog", u"\u56fe\u8868\u5c3a\u5bf8", None))
        self.lblWidth.setText(QCoreApplication.translate("ConfigDialog", u"\u5bbd\uff1a", None))
        self.lblHeight.setText(QCoreApplication.translate("ConfigDialog", u"\u9ad8\uff1a", None))
        self.lblPlotType.setText(QCoreApplication.translate("ConfigDialog", u"\u7ed8\u56fe\u7c7b\u578b", None))
        self.cmbPlotType.setItemText(0, QCoreApplication.translate("ConfigDialog", u"markers", None))
        self.cmbPlotType.setItemText(1, QCoreApplication.translate("ConfigDialog", u"lines", None))
        self.cmbPlotType.setItemText(2, QCoreApplication.translate("ConfigDialog", u"markers+lines", None))

        self.lblYAxisData.setText(QCoreApplication.translate("ConfigDialog", u"y\u8f74\u6570\u636e", None))
        self.cmbYAxisData.setItemText(0, QCoreApplication.translate("ConfigDialog", u"CDF", None))
        self.cmbYAxisData.setItemText(1, QCoreApplication.translate("ConfigDialog", u"ln(-ln(1-Median Rank))", None))

        self.lblDrawData.setText(QCoreApplication.translate("ConfigDialog", u"\u7ed8\u5236\u6570\u636e\uff1a", None))
        self.chkDrawT0.setText(QCoreApplication.translate("ConfigDialog", u"T0\u6570\u636e", None))
        self.chkDrawTx.setText(QCoreApplication.translate("ConfigDialog", u"TX\u6570\u636e", None))
        self.chkDrawShift.setText(QCoreApplication.translate("ConfigDialog", u"shift\u6570\u636e", None))
        self.lblHover.setText(QCoreApplication.translate("ConfigDialog", u"hover\u6587\u672c\u914d\u7f6e", None))
        self.btnHoverHelp.setText(QCoreApplication.translate("ConfigDialog", u"\u53ef\u7528\u914d\u7f6e\u53c2\u6570", None))
        self.editHoverTemplate.setPlainText(QCoreApplication.translate("ConfigDialog", u"<b>X\u503c:</b> %{x}<br>\n"
"<b>Y\u503c:</b> %{y}<br>\n"
"<b>\u603b\u6570</b> %{len(x)}<br>\n"
"<b>Rank</b> %{} <br>\n"
"<b>\u5206\u7ec4:</b> %{group}\n"
"", None))
        self.lblTickDecimals.setText(QCoreApplication.translate("ConfigDialog", u"tick\u5c0f\u6570\u70b9\u540e\u6570\u91cf", None))
        self.lblLabelFontSize.setText(QCoreApplication.translate("ConfigDialog", u"\u6807\u7b7e\u5b57\u53f7", None))
        self.lblHoverFontSize.setText(QCoreApplication.translate("ConfigDialog", u"hover\u6587\u672c\u5b57\u53f7", None))
        self.lblDataSource.setText(QCoreApplication.translate("ConfigDialog", u"T0\u6570\u636e\u6765\u6e90\uff1a", None))
        self.rdoDataRaw.setText(QCoreApplication.translate("ConfigDialog", u"\u539f\u59cb\u6570\u636e", None))
        self.rdoDataMerged.setText(QCoreApplication.translate("ConfigDialog", u"\u5408\u5e76\u540e\u6570\u636e", None))
        self.lblLineOpacity.setText(QCoreApplication.translate("ConfigDialog", u"\u7ebf\u900f\u660e\u5ea6", None))
        self.lblTickFormat.setText(QCoreApplication.translate("ConfigDialog", u"tick\u683c\u5f0f", None))
        self.cmbTickFormat.setItemText(0, QCoreApplication.translate("ConfigDialog", u"\u79d1\u5b66\u8bb0\u6570\u6cd5", None))
        self.cmbTickFormat.setItemText(1, QCoreApplication.translate("ConfigDialog", u"\u666e\u901a\u6570\u5b57", None))

        self.lblOutputFormat.setText(QCoreApplication.translate("ConfigDialog", u"\u9ed8\u8ba4\u8f93\u51fa\u683c\u5f0f", None))
        self.cmbOutputFormat.setItemText(0, QCoreApplication.translate("ConfigDialog", u"html", None))
        self.cmbOutputFormat.setItemText(1, QCoreApplication.translate("ConfigDialog", u"svg", None))
        self.cmbOutputFormat.setItemText(2, QCoreApplication.translate("ConfigDialog", u"jpeg", None))
        self.cmbOutputFormat.setItemText(3, QCoreApplication.translate("ConfigDialog", u"jpg", None))
        self.cmbOutputFormat.setItemText(4, QCoreApplication.translate("ConfigDialog", u"png", None))
        self.cmbOutputFormat.setItemText(5, QCoreApplication.translate("ConfigDialog", u"pdf", None))

        self.lblYscale.setText(QCoreApplication.translate("ConfigDialog", u"Y\u5750\u6807\u5c3a\u5ea6", None))
        self.cmbYScale.setItemText(0, QCoreApplication.translate("ConfigDialog", u"log", None))
        self.cmbYScale.setItemText(1, QCoreApplication.translate("ConfigDialog", u"linear", None))

        self.lblYRange.setText(QCoreApplication.translate("ConfigDialog", u"y\u8303\u56f4", None))
        self.chkYAuto.setText(QCoreApplication.translate("ConfigDialog", u"\u81ea\u52a8", None))
        self.lblYMin.setText(QCoreApplication.translate("ConfigDialog", u"min:", None))
        self.lblYMax.setText(QCoreApplication.translate("ConfigDialog", u"max:", None))
        self.lblMarkerSize.setText(QCoreApplication.translate("ConfigDialog", u"marker\u5c3a\u5bf8", None))
        self.lblMarkerframeSize.setText(QCoreApplication.translate("ConfigDialog", u"marker\u8fb9\u6846\u5bbd", None))
        self.lblXScale.setText(QCoreApplication.translate("ConfigDialog", u"X\u5750\u6807\u5c3a\u5ea6", None))
        self.cmbXScale.setItemText(0, QCoreApplication.translate("ConfigDialog", u"log", None))
        self.cmbXScale.setItemText(1, QCoreApplication.translate("ConfigDialog", u"linear", None))

        self.lblLimit.setText(QCoreApplication.translate("ConfigDialog", u"limit\u76f8\u5173", None))
        self.chkShowLimitLine.setText(QCoreApplication.translate("ConfigDialog", u"\u663e\u793alimit\u7ebf", None))
        self.chkDrawOverLimit.setText(QCoreApplication.translate("ConfigDialog", u"\u7ed8\u5236\u8d85\u51falimit\u533a\u57df", None))
        self.lblTitleFontSize.setText(QCoreApplication.translate("ConfigDialog", u"\u6807\u9898\u5b57\u53f7", None))
        self.lblWebengineScale.setText(QCoreApplication.translate("ConfigDialog", u"webengine\u9ed8\u8ba4\u7f29\u653e/%", None))
        self.tabConfig.setTabText(self.tabConfig.indexOf(self.tabPlot), QCoreApplication.translate("ConfigDialog", u"\u7ed8\u56fe\u914d\u7f6e", None))
        self.btnReadFTData.setText(QCoreApplication.translate("ConfigDialog", u"\u5237\u65b0\u6d4b\u8bd5\u9879\u6761\u76ee", None))
        self.btnOK.setText(QCoreApplication.translate("ConfigDialog", u"\u786e\u8ba4", None))
        self.btnCancel.setText(QCoreApplication.translate("ConfigDialog", u"\u53d6\u6d88", None))
    # retranslateUi

