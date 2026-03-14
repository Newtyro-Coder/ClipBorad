import os
import sys
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                             QListWidget, QListWidgetItem, QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QPixmap

class ClipboardListener(QThread):
    new_item = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.clipboard = QApplication.clipboard()
        self.last_text = ""
        self.running = True

    def run(self):
        while self.running:
            try:
                text = self.clipboard.text()
                if text and text != self.last_text:
                    self.last_text = text
                    self.new_item.emit(text)
            except Exception as e:
                print(f"剪切板读取异常:{e}")
            time.sleep(0.5)  # 轮询间隔

    def stop(self):
        self.running = False

class HistoryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("剪贴板历史")
        self.setGeometry(300, 300, 400, 300)
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def add_item(self, text):
        # 查找重复
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.text() == text:
                if i == 0:
                    return  # 已在最前，无需操作
                self.list_widget.takeItem(i)
                break

        # 插入到顶部
        new_item = QListWidgetItem(text)
        self.list_widget.insertItem(0, new_item)

        # 限制数量
        while self.list_widget.count() > 100:
            self.list_widget.takeItem(self.list_widget.count() - 1)

    def on_item_clicked(self, item):
        # 将选中项复制到剪贴板
        QApplication.clipboard().setText(item.text())

class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)

        icon_filename = "icon.jpg"
        icon_path = None

        # PyInstaller 打包后的临时目录
        if hasattr(sys, '_MEIPASS'):
            candidate = os.path.join(sys._MEIPASS, icon_filename)
            if os.path.exists(candidate):
                icon_path = candidate

        # py2app 打包后的资源目录（或其他 frozen 应用）
        elif getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            res_dir = os.path.join(exe_dir, '..', 'Resources')
            candidate = os.path.join(res_dir, icon_filename)
            if os.path.exists(candidate):
                icon_path = candidate

        # 开发环境：脚本所在目录
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            candidate = os.path.join(script_dir, icon_filename)
            if os.path.exists(candidate):
                icon_path = candidate

        if icon_path:
            icon = QIcon(icon_path)
        else:
            # 没有图标文件，生成一个纯色块作为临时图标
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.blue)   # 蓝色方块，可根据喜好修改颜色
            icon = QIcon(pixmap)
            
        self.setIcon(icon)
        self.setToolTip("剪贴板历史")
        menu = QMenu()
        show_action = QAction("显示历史", self)
        show_action.triggered.connect(parent.show_history)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(show_action)
        menu.addAction(quit_action)
        self.setContextMenu(menu)
        self.activated.connect(self.on_activated)

    def on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.parent().show_history()

class ClipboardApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出

        self.history_window = HistoryWindow()
        self.tray = TrayIcon(self)
        self.tray.show()

        # 启动监听线程
        self.listener = ClipboardListener()
        self.listener.new_item.connect(self.history_window.add_item)
        self.listener.start()

         # 连接退出清理信号
        self.aboutToQuit.connect(self.cleanup)

    def cleanup(self):
        if hasattr(self, 'listener'):
            self.listener.stop()
            self.listener.wait(1000)  # 等待线程结束（最多1秒）

    def show_history(self):
        self.history_window.show()
        self.history_window.raise_()

if __name__ == "__main__":
    app = ClipboardApp(sys.argv)
    sys.exit(app.exec_())