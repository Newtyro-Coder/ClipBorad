import sys
import logging
import platform
from core.app import HotkeyListener
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtCore import QByteArray
from ui.history_window import HistoryWindow
from ui.tray_icon import TrayIcon
from core.listener import ClipboardListener

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SingleInstanceManager:
    """管理单实例检查和激活"""
    def __init__(self, server_name="ClipboardHistoryApp"):
        self.server_name = server_name
        self.server = None

    def try_activate_existing(self):
        """尝试激活现有实例"""
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        if socket.waitForConnected(1000):
            socket.write(QByteArray(b"activate"))
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
            return True
        return False

    def start_server(self, app):
        """启动本地服务器"""
        self.server = QLocalServer(app)
        self.server.newConnection.connect(app.on_new_connection)
        QLocalServer.removeServer(self.server_name)
        if not self.server.listen(self.server_name):
            logging.warning("无法启动本地服务器，但将继续运行。")

class ClipboardApp(QApplication):
    def __init__(self, argv):
        # 单实例检查
        self.instance_manager = SingleInstanceManager()
        if self.instance_manager.try_activate_existing():
            logging.info("已有实例在运行，已激活其窗口，当前实例退出。")
            sys.exit(0)

        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)

        # 启动服务器
        self.instance_manager.start_server(self)

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

        # 设置全局快捷键
        self.hotkey_listener = HotkeyListener('<ctrl>+<alt>+v')
        self.hotkey_listener.activated.connect(self.show_history)
        self.hotkey_listener.start()

        # 退出清理
        self.aboutToQuit.connect(self.cleanup)

        # macOS 特定：确保服务器路径兼容
        if platform.system() == 'Darwin':
            logging.info("运行在 macOS 上，服务器使用默认路径。")

    def on_new_connection(self):
        """新实例连接时，读取数据并激活窗口"""
        conn = self.instance_manager.server.nextPendingConnection()
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
        try:
            if hasattr(self, 'clipboard_listener') and self.clipboard_listener.isRunning():
                self.clipboard_listener.stop()
                if not self.clipboard_listener.wait(2000):  # 增加超时
                    logging.warning("剪贴板监听器未在超时内停止。")
            if hasattr(self, 'hotkey_listener') and self.hotkey_listener.isRunning():
                self.hotkey_listener.stop()
                logging.info("资源清理完成。")
        except Exception as e:
            logging.error(f"清理过程中出错: {e}")

    def show_history(self):
        self.history_window.show()
        self.history_window.raise_()

if __name__ == "__main__":
    app = ClipboardApp(sys.argv)
    sys.exit(app.exec_())