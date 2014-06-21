#-*- coding: utf-8 -*-

import sys, time
import win32gui, win32con
import win32gui_struct
from PySide.QtGui import QWidget, QApplication
from PySide.QtCore import QThread, Signal, QObject

class MySignal(QObject):
    msg = Signal(object)

class MyThread(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.signal = MySignal()
        self.GUID_DEVINTERFACE_USB_DEVICE = "{A5DCBF10-6530-11D2-901F-00C04FB951ED}"

    def run(self):
        self.TestDeviceNotifications()

    def OnDeviceChange(self, hwnd, msg, wp, lp):
        # 將 lp 拆成適當的  DEV_BROADCAST_* 格式，使用 DEV_BROADCAST_HDR 中的自我識別資料
        info = win32gui_struct.UnpackDEV_BROADCAST(lp)

        if wp == win32con.DBT_DEVICEARRIVAL and info.devicetype == win32con.DBT_DEVTYP_VOLUME:
            self.signal.msg.emit(u'裝置已新增')
        elif wp == win32con.DBT_DEVICEREMOVECOMPLETE and info.devicetype == win32con.DBT_DEVTYP_VOLUME:
            self.signal.msg.emit(u'裝置已移除')

        return True

    def TestDeviceNotifications(self):
        wc = win32gui.WNDCLASS()
        wc.lpszClassName = 'test_devicenotify'
        wc.style =  win32con.CS_GLOBALCLASS|win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hbrBackground = win32con.COLOR_WINDOW+1
        wc.lpfnWndProc={win32con.WM_DEVICECHANGE:self.OnDeviceChange}
        class_atom=win32gui.RegisterClass(wc)
        # 產生一個不可見的視窗
        hwnd = win32gui.CreateWindow(wc.lpszClassName,
            'Testing some devices',
            win32con.WS_CAPTION,
            100,100,900,900, 0, 0, 0, None)

        hdevs = []
        # 監看所有的USB裝置通知
        filter = win32gui_struct.PackDEV_BROADCAST_DEVICEINTERFACE(self.GUID_DEVINTERFACE_USB_DEVICE)
        hdev = win32gui.RegisterDeviceNotification(hwnd, filter, win32con.DEVICE_NOTIFY_WINDOW_HANDLE)
        hdevs.append(hdev)

        # 開始 message pump，等待通知被傳遞
        while 1:
            win32gui.PumpWaitingMessages()
            time.sleep(0.01)
        win32gui.DestroyWindow(hwnd)
        win32gui.UnregisterClass(wc.lpszClassName, None)

class MyWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.thread = MyThread()
        self.thread.signal.msg.connect(self.device_changed)
        self.thread.start()

    def device_changed(self, msg):
        print 'got: '+msg


if __name__=='__main__':
    app = QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    sys.exit(app.exec_())