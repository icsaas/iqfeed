#-*-coding:utf-8-*-
from PySide import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(562, 566)
        self.label = QtGui.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(20, 20, 54, 12))
        self.label.setObjectName("label")
        self.srcPathText = QtGui.QPlainTextEdit(Dialog)
        self.srcPathText.setGeometry(QtCore.QRect(80, 10, 401, 31))
        self.srcPathText.setObjectName("srcPathText")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "多媒体信息扫描", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "视频目录", None, QtGui.QApplication.UnicodeUTF8))

class MainWindow(QtGui.QMainWindow, Ui_Dialog):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

#Main function
import sys
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainWnd = MainWindow()
    mainWnd.show()
    app.exec_()

