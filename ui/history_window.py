from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QClipboard  # 可选，但用到 QApplication

#剪切板主界面
class HistoryWindow(QWidget):
    countChanged = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("剪贴板历史 (0/100)")
        self.setGeometry(300, 300, 400, 300)
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def _get_full_text(self,item):
        """获取项目的完整文本（优先使用工具提示，回退到显示文本）"""
        return item.toolTip() or item.text()

    def _update_count_display(self):
        """更新窗口标题并发射数量信号"""
        count = self.list_widget.count()
        self.setWindowTitle(f"剪贴板历史 ({count}/100)")
        self.countChanged.emit(count)
    
    def add_item(self, text):
        # 快速检查：如果列表第一条的完整文本已经等于新文本，直接返回
        if self.list_widget.count() > 0:
            first_item = self.list_widget.item(0)
            if self._get_full_text(first_item) == text:
                return  # 已在最前，无需任何操作

        # 查找并删除重复项（使用完整文本比较）
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if self._get_full_text(item) == text:
                self.list_widget.takeItem(i)
                break
        
        # 截断显示文本（例如最多50字符）
        MAX_LENGTH = 50
        if len(text) > MAX_LENGTH:
            display_text = text[:MAX_LENGTH-3] + "..."
        else:
            display_text = text

        # 插入到顶部
        new_item = QListWidgetItem(display_text)
        new_item.setToolTip(text)  # 完整文本作为工具提示
        self.list_widget.insertItem(0, new_item)

        # 限制数量
        while self.list_widget.count() > 100:
            self.list_widget.takeItem(self.list_widget.count() - 1)

         # 更新数量显示
        self._update_count_display()

    def on_item_double_clicked(self, item):
        # 双击将选中项复制到剪贴板
        full_text = self._get_full_text(item)

        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(full_text)