import time
from PyQt5.QtCore import QThread, pyqtSignal
from pynput import keyboard

class HotkeyListener(QThread):
    """全局热键监听器（运行在独立线程）"""
    activated = pyqtSignal()

    def __init__(self, hotkey='<cmd>+<shift>+v'):
        super().__init__()
        self.hotkey = hotkey
        self.listener = None

    def run(self):
        def on_activate():
            print("✅ 热键被触发！")
            self.activated.emit()  # 通过信号通知主线程

        try:
            print(f"🔄 正在注册热键: {self.hotkey}")
            self.listener = keyboard.GlobalHotKeys({
                self.hotkey: on_activate
            })
            self.listener.start()  # 非阻塞启动
            print("✅ 热键监听已启动，等待触发...")
            # 保持线程运行，直到外部调用 stop()
            while self.listener.running:
                time.sleep(0.1)  # 避免 busy loop
        except Exception as e:
            print(f"热键监听启动失败: {e}")

    def stop(self):
        if self.listener:
            print("🛑 正在停止热键监听...")
            self.listener.stop()
            self.wait()  # 等待线程结束