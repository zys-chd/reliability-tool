# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TDDB_custom_draw.ui'
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
    QDialogButtonBox, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(796, 553)
        self.dialogLayout = QVBoxLayout(Dialog)
        self.dialogLayout.setObjectName(u"dialogLayout")
        self.gbAddItem = QGroupBox(Dialog)
        self.gbAddItem.setObjectName(u"gbAddItem")
        self.addItemLayout = QHBoxLayout(self.gbAddItem)
        self.addItemLayout.setObjectName(u"addItemLayout")
        self.lblGroup = QLabel(self.gbAddItem)
        self.lblGroup.setObjectName(u"lblGroup")

        self.addItemLayout.addWidget(self.lblGroup)

        self.cmbGroup = QComboBox(self.gbAddItem)
        self.cmbGroup.setObjectName(u"cmbGroup")

        self.addItemLayout.addWidget(self.cmbGroup)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.addItemLayout.addItem(self.horizontalSpacer)

        self.lblVoltage = QLabel(self.gbAddItem)
        self.lblVoltage.setObjectName(u"lblVoltage")

        self.addItemLayout.addWidget(self.lblVoltage)

        self.cmbVoltage = QComboBox(self.gbAddItem)
        self.cmbVoltage.setObjectName(u"cmbVoltage")

        self.addItemLayout.addWidget(self.cmbVoltage)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.addItemLayout.addItem(self.horizontalSpacer_2)

        self.lblTemp = QLabel(self.gbAddItem)
        self.lblTemp.setObjectName(u"lblTemp")

        self.addItemLayout.addWidget(self.lblTemp)

        self.cmbTemp = QComboBox(self.gbAddItem)
        self.cmbTemp.setObjectName(u"cmbTemp")

        self.addItemLayout.addWidget(self.cmbTemp)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.addItemLayout.addItem(self.horizontalSpacer_3)

        self.lblArea = QLabel(self.gbAddItem)
        self.lblArea.setObjectName(u"lblArea")

        self.addItemLayout.addWidget(self.lblArea)

        self.cmbArea = QComboBox(self.gbAddItem)
        self.cmbArea.setObjectName(u"cmbArea")

        self.addItemLayout.addWidget(self.cmbArea)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.addItemLayout.addItem(self.horizontalSpacer_4)

        self.btnAdd = QPushButton(self.gbAddItem)
        self.btnAdd.setObjectName(u"btnAdd")

        self.addItemLayout.addWidget(self.btnAdd)


        self.dialogLayout.addWidget(self.gbAddItem)

        self.gbManagedItems = QGroupBox(Dialog)
        self.gbManagedItems.setObjectName(u"gbManagedItems")
        self.managedLayout = QVBoxLayout(self.gbManagedItems)
        self.managedLayout.setObjectName(u"managedLayout")
        self.saItems = QScrollArea(self.gbManagedItems)
        self.saItems.setObjectName(u"saItems")
        self.saItems.setWidgetResizable(True)
        self.saItemsContent = QWidget()
        self.saItemsContent.setObjectName(u"saItemsContent")
        self.saItemsContent.setGeometry(QRect(0, 0, 752, 181))
        self.saItems.setWidget(self.saItemsContent)

        self.managedLayout.addWidget(self.saItems)

        self.verticalSpacer = QSpacerItem(20, 179, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.managedLayout.addItem(self.verticalSpacer)


        self.dialogLayout.addWidget(self.gbManagedItems)

        self.btnBox = QDialogButtonBox(Dialog)
        self.btnBox.setObjectName(u"btnBox")
        self.btnBox.setOrientation(Qt.Orientation.Horizontal)
        self.btnBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.dialogLayout.addWidget(self.btnBox)


        self.retranslateUi(Dialog)
        self.btnBox.accepted.connect(Dialog.accept)
        self.btnBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.gbAddItem.setTitle(QCoreApplication.translate("Dialog", u"\u6dfb\u52a0\u9879\u76ee", None))
        self.lblGroup.setText(QCoreApplication.translate("Dialog", u"group:", None))
        self.lblVoltage.setText(QCoreApplication.translate("Dialog", u"\u7535\u538b\uff1a", None))
        self.lblTemp.setText(QCoreApplication.translate("Dialog", u"\u6e29\u5ea6\uff1a", None))
        self.lblArea.setText(QCoreApplication.translate("Dialog", u"\u9762\u79ef\uff1a", None))
        self.btnAdd.setText(QCoreApplication.translate("Dialog", u"\u6dfb\u52a0", None))
        self.gbManagedItems.setTitle(QCoreApplication.translate("Dialog", u"\u5df2\u7531\u9879\u76ee\u7ba1\u7406", None))
    # retranslateUi

