# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'FTDataAnalisys.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QSplitter,
    QTabWidget, QVBoxLayout, QWidget)

class Ui_FTDataAnalysisWidget(object):
    def setupUi(self, FTDataAnalysisWidget):
        if not FTDataAnalysisWidget.objectName():
            FTDataAnalysisWidget.setObjectName(u"FTDataAnalysisWidget")
        FTDataAnalysisWidget.resize(1402, 1040)
        self.verticalLayout_2 = QVBoxLayout(FTDataAnalysisWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tabWidget = QTabWidget(FTDataAnalysisWidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.West)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout = QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.splitterMain = QSplitter(self.tab)
        self.splitterMain.setObjectName(u"splitterMain")
        self.splitterMain.setOrientation(Qt.Orientation.Horizontal)
        self.frameLeftPanel = QFrame(self.splitterMain)
        self.frameLeftPanel.setObjectName(u"frameLeftPanel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frameLeftPanel.sizePolicy().hasHeightForWidth())
        self.frameLeftPanel.setSizePolicy(sizePolicy)
        self.frameLeftPanel.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameLeftPanel.setFrameShadow(QFrame.Shadow.Raised)
        self.vlLeftPanel = QVBoxLayout(self.frameLeftPanel)
        self.vlLeftPanel.setObjectName(u"vlLeftPanel")
        self.gbT0DataSelect = QGroupBox(self.frameLeftPanel)
        self.gbT0DataSelect.setObjectName(u"gbT0DataSelect")
        self.glT0Data = QGridLayout(self.gbT0DataSelect)
        self.glT0Data.setObjectName(u"glT0Data")
        self.scrollT0FileList = QScrollArea(self.gbT0DataSelect)
        self.scrollT0FileList.setObjectName(u"scrollT0FileList")
        self.scrollT0FileList.setWidgetResizable(True)
        self.scrollT0FileListContent = QWidget()
        self.scrollT0FileListContent.setObjectName(u"scrollT0FileListContent")
        self.scrollT0FileListContent.setGeometry(QRect(0, 0, 931, 302))
        self.scrollT0FileList.setWidget(self.scrollT0FileListContent)

        self.glT0Data.addWidget(self.scrollT0FileList, 0, 0, 4, 1)

        self.btnAddT0File = QPushButton(self.gbT0DataSelect)
        self.btnAddT0File.setObjectName(u"btnAddT0File")

        self.glT0Data.addWidget(self.btnAddT0File, 0, 1, 1, 1)

        self.btnRemoveT0File = QPushButton(self.gbT0DataSelect)
        self.btnRemoveT0File.setObjectName(u"btnRemoveT0File")

        self.glT0Data.addWidget(self.btnRemoveT0File, 1, 1, 1, 1)

        self.btnClearT0Files = QPushButton(self.gbT0DataSelect)
        self.btnClearT0Files.setObjectName(u"btnClearT0Files")

        self.glT0Data.addWidget(self.btnClearT0Files, 2, 1, 1, 1)

        self.spacerT0Bottom = QSpacerItem(20, 511, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.glT0Data.addItem(self.spacerT0Bottom, 3, 1, 1, 1)


        self.vlLeftPanel.addWidget(self.gbT0DataSelect)

        self.gbTxDataSelect = QGroupBox(self.frameLeftPanel)
        self.gbTxDataSelect.setObjectName(u"gbTxDataSelect")
        self.glTxData = QGridLayout(self.gbTxDataSelect)
        self.glTxData.setObjectName(u"glTxData")
        self.btnAddTxFile = QPushButton(self.gbTxDataSelect)
        self.btnAddTxFile.setObjectName(u"btnAddTxFile")

        self.glTxData.addWidget(self.btnAddTxFile, 0, 1, 1, 1)

        self.btnRemoveTxFile = QPushButton(self.gbTxDataSelect)
        self.btnRemoveTxFile.setObjectName(u"btnRemoveTxFile")

        self.glTxData.addWidget(self.btnRemoveTxFile, 1, 1, 1, 1)

        self.btnClearTxFiles = QPushButton(self.gbTxDataSelect)
        self.btnClearTxFiles.setObjectName(u"btnClearTxFiles")

        self.glTxData.addWidget(self.btnClearTxFiles, 2, 1, 1, 1)

        self.spacerTxBottom = QSpacerItem(20, 511, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.glTxData.addItem(self.spacerTxBottom, 3, 1, 1, 1)

        self.scrollTxFileList = QScrollArea(self.gbTxDataSelect)
        self.scrollTxFileList.setObjectName(u"scrollTxFileList")
        self.scrollTxFileList.setWidgetResizable(True)
        self.scrollTxFileListContent = QWidget()
        self.scrollTxFileListContent.setObjectName(u"scrollTxFileListContent")
        self.scrollTxFileListContent.setGeometry(QRect(0, 0, 931, 303))
        self.scrollTxFileList.setWidget(self.scrollTxFileListContent)

        self.glTxData.addWidget(self.scrollTxFileList, 0, 0, 4, 1)


        self.vlLeftPanel.addWidget(self.gbTxDataSelect)

        self.gbConfigFiles = QGroupBox(self.frameLeftPanel)
        self.gbConfigFiles.setObjectName(u"gbConfigFiles")
        self.glConfig = QGridLayout(self.gbConfigFiles)
        self.glConfig.setObjectName(u"glConfig")
        self.editTxMergeFile = QLineEdit(self.gbConfigFiles)
        self.editTxMergeFile.setObjectName(u"editTxMergeFile")

        self.glConfig.addWidget(self.editTxMergeFile, 0, 1, 1, 1)

        self.btnTemplateConfig = QPushButton(self.gbConfigFiles)
        self.btnTemplateConfig.setObjectName(u"btnTemplateConfig")

        self.glConfig.addWidget(self.btnTemplateConfig, 3, 1, 1, 1)

        self.btnOpenCompareFile = QPushButton(self.gbConfigFiles)
        self.btnOpenCompareFile.setObjectName(u"btnOpenCompareFile")

        self.glConfig.addWidget(self.btnOpenCompareFile, 1, 2, 1, 1)

        self.btnPlotConfig = QPushButton(self.gbConfigFiles)
        self.btnPlotConfig.setObjectName(u"btnPlotConfig")

        self.glConfig.addWidget(self.btnPlotConfig, 3, 2, 1, 1)

        self.btnSelectCompareFile = QPushButton(self.gbConfigFiles)
        self.btnSelectCompareFile.setObjectName(u"btnSelectCompareFile")

        self.glConfig.addWidget(self.btnSelectCompareFile, 1, 3, 1, 1)

        self.btnSelectTxFile = QPushButton(self.gbConfigFiles)
        self.btnSelectTxFile.setObjectName(u"btnSelectTxFile")

        self.glConfig.addWidget(self.btnSelectTxFile, 0, 3, 1, 1)

        self.editCompareFile = QLineEdit(self.gbConfigFiles)
        self.editCompareFile.setObjectName(u"editCompareFile")

        self.glConfig.addWidget(self.editCompareFile, 1, 1, 1, 1)

        self.btnGroupConfig = QPushButton(self.gbConfigFiles)
        self.btnGroupConfig.setObjectName(u"btnGroupConfig")

        self.glConfig.addWidget(self.btnGroupConfig, 3, 0, 1, 1)

        self.btnOpenTxFile = QPushButton(self.gbConfigFiles)
        self.btnOpenTxFile.setObjectName(u"btnOpenTxFile")

        self.glConfig.addWidget(self.btnOpenTxFile, 0, 2, 1, 1)

        self.lblCompareFile = QLabel(self.gbConfigFiles)
        self.lblCompareFile.setObjectName(u"lblCompareFile")

        self.glConfig.addWidget(self.lblCompareFile, 1, 0, 1, 1)

        self.lblTxMergeFile = QLabel(self.gbConfigFiles)
        self.lblTxMergeFile.setObjectName(u"lblTxMergeFile")

        self.glConfig.addWidget(self.lblTxMergeFile, 0, 0, 1, 1)

        self.separatorConfig = QFrame(self.gbConfigFiles)
        self.separatorConfig.setObjectName(u"separatorConfig")
        self.separatorConfig.setFrameShape(QFrame.Shape.HLine)
        self.separatorConfig.setFrameShadow(QFrame.Shadow.Sunken)

        self.glConfig.addWidget(self.separatorConfig, 2, 0, 1, 4)


        self.vlLeftPanel.addWidget(self.gbConfigFiles)

        self.gbActions = QGroupBox(self.frameLeftPanel)
        self.gbActions.setObjectName(u"gbActions")
        self.hlActions = QHBoxLayout(self.gbActions)
        self.hlActions.setObjectName(u"hlActions")
        self.btnDrawExcel = QPushButton(self.gbActions)
        self.btnDrawExcel.setObjectName(u"btnDrawExcel")

        self.hlActions.addWidget(self.btnDrawExcel)

        self.btnMergeFiles = QPushButton(self.gbActions)
        self.btnMergeFiles.setObjectName(u"btnMergeFiles")

        self.hlActions.addWidget(self.btnMergeFiles)

        self.btnCompareFiles = QPushButton(self.gbActions)
        self.btnCompareFiles.setObjectName(u"btnCompareFiles")

        self.hlActions.addWidget(self.btnCompareFiles)

        self.btnPlot = QPushButton(self.gbActions)
        self.btnPlot.setObjectName(u"btnPlot")

        self.hlActions.addWidget(self.btnPlot)

        self.btnSaveImage = QPushButton(self.gbActions)
        self.btnSaveImage.setObjectName(u"btnSaveImage")

        self.hlActions.addWidget(self.btnSaveImage)

        self.btnReset = QPushButton(self.gbActions)
        self.btnReset.setObjectName(u"btnReset")

        self.hlActions.addWidget(self.btnReset)


        self.vlLeftPanel.addWidget(self.gbActions)

        self.lblStatus = QLabel(self.frameLeftPanel)
        self.lblStatus.setObjectName(u"lblStatus")

        self.vlLeftPanel.addWidget(self.lblStatus)

        self.splitterMain.addWidget(self.frameLeftPanel)
        self.gbResultDisplay = QGroupBox(self.splitterMain)
        self.gbResultDisplay.setObjectName(u"gbResultDisplay")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.gbResultDisplay.sizePolicy().hasHeightForWidth())
        self.gbResultDisplay.setSizePolicy(sizePolicy1)
        self.vlResult = QVBoxLayout(self.gbResultDisplay)
        self.vlResult.setObjectName(u"vlResult")
        self.webResult = QWebEngineView(self.gbResultDisplay)
        self.webResult.setObjectName(u"webResult")
        self.webResult.setUrl(QUrl(u"about:blank"))

        self.vlResult.addWidget(self.webResult)

        self.splitterMain.addWidget(self.gbResultDisplay)

        self.verticalLayout.addWidget(self.splitterMain)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_5 = QVBoxLayout(self.tab_2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.splitter = QSplitter(self.tab_2)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.groupBox = QGroupBox(self.splitter)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.splitter.addWidget(self.groupBox)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout_4 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.groupBox_2 = QGroupBox(self.layoutWidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout = QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.webEngineView = QWebEngineView(self.groupBox_2)
        self.webEngineView.setObjectName(u"webEngineView")
        self.webEngineView.setUrl(QUrl(u"about:blank"))

        self.gridLayout.addWidget(self.webEngineView, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 421, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 0, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 1, 0, 1, 1)


        self.verticalLayout_4.addWidget(self.groupBox_2)

        self.groupBox_3 = QGroupBox(self.layoutWidget)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.scrollArea = QScrollArea(self.groupBox_3)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 774, 448))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_3.addWidget(self.scrollArea)


        self.verticalLayout_4.addWidget(self.groupBox_3)

        self.splitter.addWidget(self.layoutWidget)

        self.verticalLayout_5.addWidget(self.splitter)

        self.tabWidget.addTab(self.tab_2, "")

        self.verticalLayout_2.addWidget(self.tabWidget)


        self.retranslateUi(FTDataAnalysisWidget)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(FTDataAnalysisWidget)
    # setupUi

    def retranslateUi(self, FTDataAnalysisWidget):
        FTDataAnalysisWidget.setWindowTitle(QCoreApplication.translate("FTDataAnalysisWidget", u"Form", None))
        self.gbT0DataSelect.setTitle(QCoreApplication.translate("FTDataAnalysisWidget", u"T0\u6570\u636e\u9009\u62e9", None))
        self.btnAddT0File.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u6dfb\u52a0\u6587\u4ef6", None))
        self.btnRemoveT0File.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u5220\u9664\u5355\u4e2a\u6587\u4ef6", None))
        self.btnClearT0Files.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u5220\u9664\u5168\u90e8\u6587\u4ef6", None))
        self.gbTxDataSelect.setTitle(QCoreApplication.translate("FTDataAnalysisWidget", u"TX\u6570\u636e\u9009\u62e9", None))
        self.btnAddTxFile.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u6dfb\u52a0\u6587\u4ef6", None))
        self.btnRemoveTxFile.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u5220\u9664\u5355\u4e2a\u6587\u4ef6", None))
        self.btnClearTxFiles.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u5220\u9664\u5168\u90e8\u6587\u4ef6", None))
        self.gbConfigFiles.setTitle(QCoreApplication.translate("FTDataAnalysisWidget", u"\u914d\u7f6e\u6587\u4ef6", None))
        self.btnTemplateConfig.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u6a21\u677f\u914d\u7f6e", None))
        self.btnOpenCompareFile.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u6253\u5f00", None))
        self.btnPlotConfig.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u7ed8\u56fe\u914d\u7f6e", None))
        self.btnSelectCompareFile.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u9009\u62e9", None))
        self.btnSelectTxFile.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u9009\u62e9", None))
        self.btnGroupConfig.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u5206\u7ec4\u914d\u7f6e", None))
        self.btnOpenTxFile.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u6253\u5f00", None))
        self.lblCompareFile.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u5bf9\u6bd4\u7ed3\u679c\uff1a", None))
        self.lblTxMergeFile.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u5408\u5e76\u7ed3\u679c\uff1a", None))
        self.gbActions.setTitle(QCoreApplication.translate("FTDataAnalysisWidget", u"\u529f\u80fd", None))
        self.btnDrawExcel.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u7ed8\u5236excel", None))
        self.btnMergeFiles.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u5408\u5e76\u6587\u4ef6", None))
        self.btnCompareFiles.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u5bf9\u6bd4\u6587\u4ef6", None))
        self.btnPlot.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u7ed8\u56fe", None))
        self.btnSaveImage.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u4fdd\u5b58\u56fe\u7247", None))
        self.btnReset.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u91cd\u7f6e\u6240\u6709", None))
        self.lblStatus.setText(QCoreApplication.translate("FTDataAnalysisWidget", u"\u5c31\u7eea", None))
        self.gbResultDisplay.setTitle(QCoreApplication.translate("FTDataAnalysisWidget", u"\u7ed3\u679c\u663e\u793a", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("FTDataAnalysisWidget", u"\u6279\u91cf\u7ed8\u5236", None))
        self.groupBox.setTitle(QCoreApplication.translate("FTDataAnalysisWidget", u"\u6570\u636e\u9009\u62e9", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("FTDataAnalysisWidget", u"\u7ed8\u56fe", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("FTDataAnalysisWidget", u"\u7edf\u8ba1\u6570\u636e", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("FTDataAnalysisWidget", u"\u5355\u4e2a\u5206\u6790", None))
    # retranslateUi

