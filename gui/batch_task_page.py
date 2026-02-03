import os
from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView, QWidget, QVBoxLayout, \
    QHBoxLayout, QPushButton, QLabel, QFileDialog, QTableWidgetItem, QProgressBar, QLineEdit, QMessageBox, QFrame

from controller.gui_controller import GUIController


# noinspection PyAttributeOutsideInit
class BatchTaskPage(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller: GUIController = controller

        self.setup_ui()

        self.bind_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        self.layout = layout

        # A. 顶部操作栏
        self.setup_top_bar_section()

        # B. 任务表格
        self.setup_table_section()

        # C. 导出路径
        self.setup_output_section()

        # D. 底部操作区
        self.setup_bottom_section()

    def setup_top_bar_section(self):
        top_bar = QHBoxLayout()
        self.btn_add_files = QPushButton("➕ 添加文件")
        self.btn_add_dir = QPushButton("📁 添加文件夹")
        self.btn_clear = QPushButton("🗑️ 清空列表")
        self.btn_remove_sel = QPushButton("❌ 移除选中")

        top_bar.addWidget(self.btn_add_files)
        top_bar.addWidget(self.btn_add_dir)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_remove_sel)
        top_bar.addWidget(self.btn_clear)

        self.layout.addLayout(top_bar)

    def setup_table_section(self):
        self.table_container = QFrame()
        self.table_container.setObjectName("BatchTableContainer")
        container_layout = QVBoxLayout(self.table_container)
        container_layout.setContentsMargins(2, 2, 2, 2)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["源文件名", "大小", "状态"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setFrameShape(QFrame.Shape.NoFrame)

        container_layout.addWidget(self.table)
        self.layout.addWidget(self.table_container)

    def setup_output_section(self):
        layout = QHBoxLayout()
        self.lbl_output = QLabel("导出目录:")
        self.edit_output = QLineEdit()
        self.edit_output.setPlaceholderText("请选择导出目录")
        self.edit_output.setReadOnly(True)
        self.btn_browse_output = QPushButton("选择目录")

        layout.addWidget(self.lbl_output)
        layout.addWidget(self.edit_output)
        layout.addWidget(self.btn_browse_output)
        self.layout.addLayout(layout)

    # noinspection DuplicatedCode
    def setup_bottom_section(self):
        bottom_container = QVBoxLayout()

        # 总体进度信息
        status_info_layout = QHBoxLayout()
        self.lbl_batch_status = QLabel("就绪")
        self.lbl_batch_percent = QLabel("0 / 0")
        status_info_layout.addWidget(self.lbl_batch_status)
        status_info_layout.addStretch()
        status_info_layout.addWidget(self.lbl_batch_percent)

        # 进度条
        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setTextVisible(False)
        self.batch_progress_bar.setRange(0, 100)
        self.batch_progress_bar.setValue(0)

        # 执行按钮
        self.btn_start_batch = QPushButton("开始批量解码")
        self.btn_start_batch.setObjectName("ActionBtn")
        self.btn_start_batch.setFixedHeight(45)
        self.btn_start_batch.setEnabled(False)

        # 组合布局
        bottom_container.addLayout(status_info_layout)
        bottom_container.addWidget(self.batch_progress_bar)
        bottom_container.addSpacing(10)
        bottom_container.addWidget(self.btn_start_batch)

        self.layout.addLayout(bottom_container)

    def bind_signals(self):
        self.btn_add_files.clicked.connect(self.on_add_files_clicked)
        self.btn_add_dir.clicked.connect(self.on_add_dir_clicked)
        self.btn_browse_output.clicked.connect(self.on_output_clicked)
        self.btn_clear.clicked.connect(self.clear_table)
        self.btn_remove_sel.clicked.connect(self.remove_selected)
        self.btn_start_batch.clicked.connect(self.on_start_batch_clicked)

        self.controller.signal_batch_update_progress.connect(self.on_batch_update_progress)
        self.controller.signal_batch_decryption_finished.connect(self.on_batch_decryption_finished)

    def on_add_files_clicked(self):
        """手动点击添加文件按钮"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择 NCM 文件", "", "网易云音乐加密文件 (*.ncm)"
        )
        if files:
            self.add_files_to_list(files)

    def on_add_dir_clicked(self):
        """选择文件夹并扫描其中的 NCM 文件"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择包含 NCM 文件的文件夹")
        if not dir_path:
            return

        # 遍历文件夹
        ncm_files = []
        # os.walk 可以递归遍历子文件夹
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.lower().endswith(".ncm"):
                    full_path = os.path.join(root, file)
                    ncm_files.append(full_path)

        if ncm_files:
            self.add_files_to_list(ncm_files)
        else:
            self.show_message_dialog("info", "未找到.ncm文件")

    def on_output_clicked(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if dir_path:
            self.edit_output.setText(dir_path)
            self.controller.set_batch_output_file(dir_path)

    def on_start_batch_clicked(self):
        tasks = []
        for row in range(self.table.rowCount()):
            path = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            tasks.append((row, path))

        if tasks:
            count = self.table.rowCount()
            self.lbl_batch_status.setText(f"正在解码")
            self.lbl_batch_percent.setText(f"0 / {count}")
            self.btn_start_batch.setEnabled(False)
            self.controller.start_batch_decryption(tasks)

    @Slot(int, str)
    def on_batch_update_progress(self, row_idx, msg):
        self.update_item_status(row_idx, msg)
        if msg == "完成":
            self.update_overall_progress(row_idx + 1, self.table.rowCount())

    @Slot(int)
    def on_batch_decryption_finished(self, total):
        self.show_message_dialog("info", "批量解码任务全部完成！")
        self.update_overall_progress(total, total)
        self.btn_start_batch.setEnabled(True)

    @Slot(str, str)
    def show_message_dialog(self, level, msg):
        if level == "error":
            QMessageBox.critical(self, "错误", msg)
        else:
            QMessageBox.information(self, "提示", msg)

    def handle_drop_event(self, urls):
        """处理来自主窗口分发的拖拽事件"""
        file_paths = [u.toLocalFile() for u in urls]
        valid_paths = []

        for path in file_paths:
            p = Path(path)
            if p.is_file() and p.suffix.lower() == ".ncm":
                valid_paths.append(path)
            elif p.is_dir():
                # 如果拖入的是文件夹，递归查找
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(".ncm"):
                            valid_paths.append(os.path.join(root, file))

        self.add_files_to_list(valid_paths)

    def add_files_to_list(self, paths):
        """将路径解析并添加到表格"""
        for path in paths:
            if not path.lower().endswith(".ncm"):
                continue

            # 转成绝对路径再做查重和插入
            path = str(Path(path).resolve().absolute())

            # 查重逻辑：避免重复添加同一个文件
            if self._is_already_in_list(path):
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            path_obj = Path(path)
            file_size = os.path.getsize(path) / (1024 * 1024)  # MB

            # 填充单元格
            # 第0列存文件名，并关联 UserRole 存储全路径
            name_item = QTableWidgetItem(path_obj.name)
            name_item.setData(Qt.ItemDataRole.UserRole, path)

            self.table.setItem(row, 0, name_item)

            size_item = QTableWidgetItem(f"{file_size:.2f} MB")
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, size_item)

            status_item = QTableWidgetItem("等待中")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, status_item)

        self._update_ui_state()

    def _is_already_in_list(self, path):
        """检查路径是否已存在于表格中"""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).data(Qt.ItemDataRole.UserRole) == path:
                return True
        return False

    def _update_ui_state(self):
        """根据表格内容更新按钮和标签状态"""
        count = self.table.rowCount()
        self.lbl_batch_status.setText(f"待处理文件: {count}")
        self.lbl_batch_percent.setText(f"0 / {count}")
        self.btn_start_batch.setEnabled(count > 0)

    def update_overall_progress(self, current, total):
        """更新底部进度条"""
        self.lbl_batch_percent.setText(f"{current} / {total}")
        if total > 0:
            percent = int((current / total) * 100)
            self.batch_progress_bar.setValue(percent)

        if current == total:
            self.lbl_batch_status.setText("全部任务已完成")
            self.btn_start_batch.setEnabled(True)

    def update_item_status(self, row, status_text):
        """更新表格中某一行的状态文本"""
        # 更新状态列
        status_item = self.table.item(row, 2)
        if status_item:
            status_item.setText(status_text)

    def clear_table(self):
        self.table.setRowCount(0)
        self.batch_progress_bar.setValue(0)
        self._update_ui_state()

    def remove_selected(self):
        selected_ranges = self.table.selectedRanges()
        # 从后往前删，避免索引错乱
        rows_to_delete = set()
        for r in selected_ranges:
            for row in range(r.topRow(), r.bottomRow() + 1):
                rows_to_delete.add(row)

        for row in sorted(list(rows_to_delete), reverse=True):
            self.table.removeRow(row)
        self.batch_progress_bar.setValue(0)
        self._update_ui_state()
