from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSlider


class VolumePopup(QWidget):
    """弹出式音量滑动条窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置窗口标志为无边框、工具提示风格
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 10, 5, 20)

        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setRange(0, 100)
        self.slider.setFixedSize(20, 120)

        # 美化滑块样式
        self.slider.setStyleSheet("""
            QSlider::groove:vertical {
                background: #f0f0f0;
                width: 4px;
                border-radius: 2px;
            }

            QSlider::sub-page:vertical {
                background: #f0f0f0;
                width: 4px;
                border-radius: 2px;
            }

            QSlider::add-page:vertical {
                background: #409eff;
                width: 4px;
                border-radius: 2px;
            }

            QSlider::handle:vertical { 
                background: #409eff; 
                height: 12px; 
                width: 12px; 
                margin: 0 -4px; 
                border-radius: 6px; 
            }
            
            QSlider::handle:vertical:hover {
                background: #66b1ff;
            }
        """)

        self.layout.addWidget(self.slider)
        self.setFixedSize(30, 150)

    def paintEvent(self, event):
        """绘制带尖角的白底气泡"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 抗锯齿

        # 定义气泡主体的矩形区域
        arrow_height = 10
        rect = self.rect().adjusted(1, 1, -1, -arrow_height - 1)

        # 创建路径
        path = QPainterPath()
        radius = 8
        # 绘制圆角矩形主体
        path.addRoundedRect(rect, radius, radius)

        # 绘制底部的三角形尖角
        center_x = self.width() // 2
        path.moveTo(center_x - 8, rect.bottom())  # 尖角左起点
        path.lineTo(center_x, self.height() - 2)  # 尖角顶点 (指向按钮)
        path.lineTo(center_x + 8, rect.bottom())  # 尖角右终点

        # 填充背景颜色 (纯白)
        painter.fillPath(path, QColor("white"))

        # 灰色描边
        pen = QPen(QColor("#dcdfe6"), 1)
        painter.setPen(pen)
        painter.drawPath(path)
