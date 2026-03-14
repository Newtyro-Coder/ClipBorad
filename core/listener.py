import time
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

#后台线程，监听系统剪切板
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