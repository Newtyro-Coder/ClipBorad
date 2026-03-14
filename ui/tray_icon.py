import os
import sys
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt


#系统托盘图标与交互菜单
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
        self.show_action = QAction("显示历史 (0/100)", self)
        self.show_action.triggered.connect(parent.show_history)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)

        menu.addAction(self.show_action)
        menu.addAction(quit_action)
        self.setContextMenu(menu)
        self.activated.connect(self.on_activated)

    def update_show_action_text(self, count):
        """更新菜单项中的数量显示"""
        self.show_action.setText(f"显示历史 ({count}/100)")

    def on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.parent().show_history()