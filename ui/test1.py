import sys
from PySide import QtCore,QtGui

# class MainWindow(QtGui.QMainWindow):
#     def closeEvent(self,event):
#         event.ignore()
#         self.hide()
#         self.trayicon.showMessage("Running",'Running in the background')
#     def hideEvent(self,event):
#         event.ignore()
#         self.move(0,0)
#

app=QtGui.QApplication(sys.argv)
button=QtGui.QPushButton('Quit')
QtCore.QObject.connect(button,QtCore.SIGNAL('clicked()'),
                       button,QtCore.SLOT('close()'))

button.show()
sys.exit(app.exec_())