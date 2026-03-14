from PyQt5.QtWidgets import QApplication
from ui.history_window import HistoryWindow
from ui.tray_icon import TrayIcon
from core.listener import ClipboardListener

#管理进程生命周期
class ClipboardApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出

        self.history_window = HistoryWindow()
        self.tray = TrayIcon(self)
        self.tray.show()

        # 连接数量变化信号到托盘菜单更新
        self.history_window.countChanged.connect(self.tray.update_show_action_text)

        # 启动监听线程
        self.listener = ClipboardListener()
        self.listener.new_item.connect(self.history_window.add_item)
        self.listener.start()

         # 连接退出清理信号
        self.aboutToQuit.connect(self.cleanup)

        # 初始化数量显示（发射一次信号，使托盘菜单显示正确）
        self.history_window._update_count_display()

    def cleanup(self):
        if hasattr(self, 'listener'):
            self.listener.stop()
            self.listener.wait(1000)  # 等待线程结束（最多1秒）

    def show_history(self):
        self.history_window.show()
        self.history_window.raise_()