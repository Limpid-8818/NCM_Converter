import os
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QTabWidget

from controller.gui_controller import GUIController
from gui.batch_task_page import BatchTaskPage
from gui.main_page import MainPage


def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# noinspection PyAttributeOutsideInit
class NCMConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # 实例化控制器
        self.controller = GUIController()

        # 初始化UI
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("NCM 音频解码转换工具")
        self.setMinimumSize(700, 625)
        icon_path = get_resource_path("resources/NCMCicon.ico")
        self.setWindowIcon(QIcon(str(icon_path)))

        # 全局主部件
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)

        # 实例化页面并添加进主部件
        self.page_single = MainPage(self.controller)
        self.page_batch = BatchTaskPage(self.controller)
        self.central_widget.addTab(self.page_single, "单文件解析")
        self.central_widget.addTab(self.page_batch, "批量解析")

        # 美化样式
        self.setStyleSheet("""
                    QMainWindow { background-color: #f5f6f7; }
                    QFrame#PreviewContainer { 
                        background-color: white; 
                        border: 1px solid #dcdfe6; 
                        border-radius: 8px; 
                    }
                    QPushButton#ActionBtn {
                        background-color: #409eff;
                        color: white;
                        border-radius: 4px;
                        font-weight: bold;
                        padding: 8px 20px;
                    }
                    QPushButton#ActionBtn:hover { background-color: #66b1ff; }
                    QPushButton#ActionBtn:disabled { background-color: #a0cfff; }
                    QLineEdit { border: 1px solid #dcdfe6; border-radius: 4px; padding: 5px; }
                    
                    /* 批量表格外框 */
                    QFrame#BatchTableContainer {
                        background-color: white;
                        border: 1px solid #dcdfe6;
                        border-radius: 8px;
                    }
        
                    /* 表格整体样式 */
                    QTableWidget {
                        background-color: transparent; /* 背景透明，显示 Container 的白色 */
                        gridline-color: #f0f0f0;       /* 网格线颜色调淡 */
                        selection-background-color: #ecf5ff; /* 选中时的背景色：浅蓝色 */
                        selection-color: #409eff;            /* 选中时的文字色：深蓝色 */
                        outline: none;                       /* 去掉选中时的虚线框 */
                    }
        
                    /* 表头样式 */
                    QHeaderView::section {
                        background-color: #f5f7fa;
                        padding: 8px;
                        border: none;
                        border-right: 1px solid #ebeef5;
                        border-bottom: 1px solid #ebeef5;
                        color: #909399;
                        font-weight: bold;
                    }
                    /* 优化选中后的条状样式，解决文字重叠感 */
                    QTableWidget::item:selected {
                        background-color: #ecf5ff;
                        color: #409eff;
                        border-bottom: 1px solid #d9ecff;
                    }
                    /* 修改表格全选方块样式 */
                    QTableWidget QTableCornerButton::section {
                        background-color: #f5f7fa; /* 与表头背景色一致 */
                        border: none;
                        border-right: 1px solid #ebeef5;
                        border-bottom: 1px solid #ebeef5;
                    }
                """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()

        if not urls:
            return

        if len(urls) > 1 or Path(urls[0].toLocalFile()).is_dir():
            self.central_widget.setCurrentIndex(1)
            self.page_batch.handle_drop_event(urls)
            return

        if self.central_widget.currentIndex() == 0:
            self.page_single.handle_drop_event(urls)
        else:
            self.page_batch.handle_drop_event(urls)
