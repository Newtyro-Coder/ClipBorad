import sys
from core.app import HotkeyListener
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtCore import QByteArray
from ui.history_window import HistoryWindow
from ui.tray_icon import TrayIcon
from core.listener import ClipboardListener

class ClipboardApp(QApplication):
    def __init__(self, argv):
         # ---------- 单实例检查 ----------
        # 尝试连接已有实例，如果成功则激活后退出
        if self.try_activate_existing():
            print("已有实例在运行，已激活其窗口，当前实例退出。")
            sys.exit(0)
        # --------------------------------

        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)

        # 创建本地服务器，用于接收新实例的激活请求
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self.on_new_connection)
        # 移除可能残留的服务器文件（Unix/Linux）或清理命名管道
        QLocalServer.removeServer("ClipboardHistoryApp")
        if not self.server.listen("ClipboardHistoryApp"):
            print("警告：无法启动本地服务器，但将继续运行。")

        # 创建界面组件
        self.history_window = HistoryWindow()
        self.tray = TrayIcon(self)
        self.tray.show()

        # 连接信号
        self.history_window.countChanged.connect(self.tray.update_show_action_text)

        # 启动剪贴板监听线程
        self.clipboard_listener = ClipboardListener()
        self.clipboard_listener.new_item.connect(self.history_window.add_item)
        self.clipboard_listener.start()

        # 初始化数量显示
        self.history_window._update_count_display()

        # 设置全局快捷键（使用 pynput）
        self.hotkey_listener = HotkeyListener('<ctrl>+<alt>+v')  # control+alt+v
        self.hotkey_listener.activated.connect(self.show_history)
        self.hotkey_listener.start()

        # 退出清理
        self.aboutToQuit.connect(self.cleanup)

    def try_activate_existing(self):
        """尝试连接已有实例，如果成功则发送激活信号并返回True"""
        socket = QLocalSocket()
        socket.connectToServer("ClipboardHistoryApp")
        if socket.waitForConnected(1000):
            # 连接成功，发送激活命令
            socket.write(QByteArray(b"activate"))
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
            return True
        return False

    def on_new_connection(self):
        """新实例连接时，读取数据并激活窗口"""
        conn = self.server.nextPendingConnection()
        if conn:
            conn.readyRead.connect(lambda: self.handle_activation(conn))
            conn.disconnected.connect(conn.deleteLater)

    def handle_activation(self, conn):
        """处理激活请求，显示窗口"""
        data = conn.readAll()
        if data == b"activate":
            self.show_history()
        conn.disconnectFromServer()

    def cleanup(self):
        """应用退出前清理资源"""
        if hasattr(self, 'clipboard_listener'):
            self.clipboard_listener.stop()
            self.clipboard_listener.wait(1000)
        if hasattr(self, 'hotkey_listener')and self.hotkey_listener.isRunning():
            self.hotkey_listener.stop()

    def show_history(self):
        self.history_window.show()
        self.history_window.raise_()

if __name__ == "__main__":
    app = ClipboardApp(sys.argv)
    sys.exit(app.exec_())