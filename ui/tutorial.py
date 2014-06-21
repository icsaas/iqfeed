import sys
from PySide.QtCore import *
from PySide.QtGui import *

#Create a At application
app=QApplication(sys.argv)
#Create a Label and show it
label=QLabel("<font color=red size=40>hello World</font>")
label.show()
#Enter Qt application main loop
app.exec_()
sys.exit()