from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Slot, QEvent, QPoint
from PySide6.QtGui import QFont, QImage, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QVBoxLayout, QFormLayout, \
    QProgressBar, QSlider, QFileDialog, QMessageBox

from controller.gui_controller import GUIController
from domain.models import NCMMetadata
from gui.widgets import VolumePopup


# noinspection PyAttributeOutsideInit
class MainPage(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller: GUIController = controller

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        self.setup_ui()

        # 绑定信号
        self.bind_signals()

    def setup_ui(self):
        # A. 文件输入区
        self.setup_input_section()

        # B. 中间预览展示区
        self.setup_preview_section()

        # C. 导出路径区
        self.setup_output_section()

        # D. 底部进度与执行区
        self.setup_bottom_section()

    def setup_input_section(self):
        layout = QHBoxLayout()
        self.lbl_input = QLabel("源文件路径:")
        self.edit_input = QLineEdit()
        self.edit_input.setPlaceholderText("请选择或拖入 .ncm 文件...")
        self.edit_input.setReadOnly(True)
        self.btn_browse_input = QPushButton("浏览")

        layout.addWidget(self.lbl_input)
        layout.addWidget(self.edit_input)
        layout.addWidget(self.btn_browse_input)
        self.main_layout.addLayout(layout)

    def setup_preview_section(self):
        # 使用QFrame包裹
        self.preview_container = QFrame()
        self.preview_container.setObjectName("PreviewContainer")
        preview_layout = QHBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        preview_layout.setSpacing(30)

        # 左侧：封面预览
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(240, 240)
        self.cover_label.setStyleSheet("background-color: #ebeef5; border-radius: 4px;")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setText("封面预览")

        # 信息展示 + 播放器布局
        info_right_layout = QVBoxLayout()

        # 元数据表单布局
        self.info_form = QFormLayout()
        self.info_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.info_form.setVerticalSpacing(12)

        self.val_title = QLabel("--")
        self.val_artist = QLabel("--")
        self.val_album = QLabel("--")
        self.val_format = QLabel("--")
        self.val_duration = QLabel("--")
        self.val_bitrate = QLabel("--")

        # 设置字体加粗
        info_font = QFont()
        info_font.setBold(True)

        for label, widget in [("标题:", self.val_title),
                              ("艺术家:", self.val_artist),
                              ("专辑:", self.val_album),
                              ("格式:", self.val_format),
                              ("时长:", self.val_duration),
                              ("比特率:", self.val_bitrate)]:
            widget.setFont(info_font)
            self.info_form.addRow(QLabel(label), widget)

        info_right_layout.addLayout(self.info_form)

        # 播放器
        info_right_layout.addStretch()
        self.player_placeholder = QFrame()
        self.player_placeholder.setMinimumHeight(60)
        info_right_layout.addWidget(self.player_placeholder)
        self.setup_player_ui()

        preview_layout.addWidget(self.cover_label)
        preview_layout.addLayout(info_right_layout)

        self.main_layout.addWidget(self.preview_container)

    def setup_output_section(self):
        layout = QHBoxLayout()
        self.lbl_output = QLabel("导出目录:")
        self.edit_output = QLineEdit()
        self.edit_output.setPlaceholderText("默认保存在源文件同级目录")
        self.edit_output.setReadOnly(True)
        self.btn_browse_output = QPushButton("选择目录")

        layout.addWidget(self.lbl_output)
        layout.addWidget(self.edit_output)
        layout.addWidget(self.btn_browse_output)
        self.main_layout.addLayout(layout)

    # noinspection DuplicatedCode
    def setup_bottom_section(self):
        bottom_layout = QVBoxLayout()

        # 进度信息
        status_layout = QHBoxLayout()
        self.lbl_status = QLabel("就绪")
        self.lbl_percent = QLabel("0%")
        status_layout.addWidget(self.lbl_status)
        status_layout.addStretch()
        status_layout.addWidget(self.lbl_percent)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # 开始按钮
        self.btn_start = QPushButton("开始解码")
        self.btn_start.setObjectName("ActionBtn")
        self.btn_start.setFixedHeight(45)
        self.btn_start.setEnabled(False)  # 初始禁用

        bottom_layout.addLayout(status_layout)
        bottom_layout.addWidget(self.progress_bar)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(self.btn_start)

        self.main_layout.addLayout(bottom_layout)

    def setup_player_ui(self):
        # 播放器组件
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        inner_layout = QHBoxLayout(self.player_placeholder)
        inner_layout.setContentsMargins(10, 5, 10, 5)

        # 播放器UI控件
        self.btn_play = QPushButton("▶️")
        self.btn_play.setFixedSize(35, 35)
        self.btn_play.setCursor(Qt.CursorShape.PointingHandCursor)

        self.slider_progress = QSlider(Qt.Orientation.Horizontal)

        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setStyleSheet("font-family: 'Consolas'; font-size: 11px;")

        self.volume_popup = VolumePopup(self)
        self.volume_popup.hide()
        self.btn_volume = QPushButton("🔊")
        self.btn_volume.setFixedSize(30, 30)
        self.btn_volume.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_volume.setFlat(True)
        self.volume_popup.slider.setValue(30)
        self.update_volume(self.volume_popup.slider.value())
        self.btn_volume.installEventFilter(self)
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.volume_popup.installEventFilter(self)

        # 将控件添加到播放器占位符布局
        inner_layout.addWidget(self.btn_play)
        inner_layout.addWidget(self.slider_progress)
        inner_layout.addWidget(self.lbl_time)
        inner_layout.addWidget(self.btn_volume)

        self.player_placeholder.setStyleSheet("""
                QFrame {
                    background-color: #f0f2f5; 
                    border: 1px solid #e4e7ed; 
                    border-radius: 6px;
                }
            """)

        # 初始状态不可用
        self.btn_play.setEnabled(False)
        self.slider_progress.setEnabled(False)

    def refresh_progress(self):
        self.lbl_status.setText("就绪")
        self.lbl_percent.setText("0%")
        self.progress_bar.setValue(0)

    def refresh_player(self):
        self.btn_play.setEnabled(False)
        self.btn_play.setText("▶️")
        self.slider_progress.setEnabled(False)
        self.slider_progress.setValue(0)
        self.lbl_time.setText("00:00 / 00:00")
        self.media_player.pause()

    def bind_signals(self):
        # UI操作触发控制器
        self.btn_browse_input.clicked.connect(self.on_input_clicked)
        self.btn_browse_output.clicked.connect(self.on_output_clicked)
        self.btn_start.clicked.connect(self.controller.start_decrypt)

        # 控制器更新UI
        self.controller.signal_update_progress.connect(self.update_progress_ui)
        self.controller.signal_update_metadata.connect(self.update_metadata_ui)
        self.controller.signal_update_cover_bytes.connect(self.update_cover_ui)
        self.controller.signal_show_message.connect(self.show_message_dialog)
        self.controller.signal_set_export_btn_enabled.connect(self.btn_start.setEnabled)
        self.controller.signal_decryption_finished.connect(self.on_decryption_finished)

        # 播放器控制器
        self.connect_player_signals()

    def on_input_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 NCM 文件", "", "网易云音乐加密文件 (*.ncm)"
        )
        if file_path:
            self.edit_input.setText(file_path)
            self.controller.set_input_file(file_path)
            self.refresh_progress()
            self.refresh_player()

    def on_output_clicked(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if dir_path:
            self.edit_output.setText(dir_path)
            self.controller.set_output_file(dir_path)

    @Slot(int, int, str)
    def update_progress_ui(self, current, total, msg):
        self.progress_bar.setValue(current)
        self.lbl_percent.setText(f"{current}%")
        self.lbl_status.setText(msg)

    @Slot(NCMMetadata)
    def update_metadata_ui(self, metadata: NCMMetadata):
        duration_str = f"{metadata.duration // 60000}分{metadata.duration % 60000 // 1000}秒" if hasattr(metadata,
                                                                                                         "duration") else "--"
        self.val_title.setText(metadata.title if hasattr(metadata, 'title') else "未知标题")
        self.val_artist.setText(', '.join(metadata.artist) if hasattr(metadata, 'artist') else "未知歌手")
        self.val_album.setText(metadata.album if hasattr(metadata, 'album') else "未知专辑")
        self.val_format.setText(metadata.format.upper() if hasattr(metadata, 'format') else "未知")
        self.val_duration.setText(duration_str)
        self.val_bitrate.setText(f"{metadata.bitrate // 1000}kbps" if hasattr(metadata, 'bitrate') else "--")

    @Slot(bytes)
    def update_cover_ui(self, cover_bytes: bytes):
        if not cover_bytes:
            return
        # 将字节流转换为 QPixmap
        image = QImage.fromData(cover_bytes)
        pixmap = QPixmap.fromImage(image)
        # 缩放图片以适应 Label，保持比例
        scaled_pixmap = pixmap.scaled(
            self.cover_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.cover_label.setPixmap(scaled_pixmap)
        self.cover_label.setText("")  # 移除文字提示

    @Slot(str, str)
    def show_message_dialog(self, level, msg):
        if level == "error":
            QMessageBox.critical(self, "错误", msg)
        else:
            QMessageBox.information(self, "提示", msg)

    @Slot(str)
    def on_decryption_finished(self, output_path):
        if output_path:
            file_url = Path(output_path).resolve().absolute().as_uri()
            self.media_player.setSource(file_url)

            self.btn_play.setEnabled(True)
            self.slider_progress.setEnabled(True)
            self.btn_play.setText("▶️")

    def handle_drop_event(self, urls):
        file_path = urls[0].toLocalFile()
        if file_path.endswith(".ncm"):
            self.edit_input.setText(file_path)
            self.controller.set_input_file(file_path)
            self.refresh_progress()
            self.refresh_player()
        else:
            self.show_message_dialog("info", "请选择.ncm文件")

    def eventFilter(self, obj, event):
        if obj == self.btn_volume or obj == self.volume_popup:
            if event.type() == QEvent.Type.Enter:
                # 不管是进到图标还是进到滑块，都保留弹窗
                self.hide_timer.stop()
                self.show_volume_popup()
                return True

            elif event.type() == QEvent.Type.Leave:
                # 250 毫秒时间移到滑块上
                self.hide_timer.start(250)
                return True

        return super().eventFilter(obj, event)

    def connect_player_signals(self):
        # 播放/暂停逻辑
        self.btn_play.clicked.connect(self.toggle_playback)
        self.media_player.mediaStatusChanged.connect(self.on_play_finished)  # 播放完成后修改按钮状态

        # 播放器进度 -> 滑块
        self.media_player.positionChanged.connect(self.sync_slider_position)
        self.media_player.durationChanged.connect(self.sync_slider_range)

        # 用户拖动滑块 -> 播放器跳转
        self.slider_progress.sliderMoved.connect(self.seek_position)

        # 音量控制
        self.volume_popup.slider.valueChanged.connect(self.update_volume)

        # 音量条显示
        self.hide_timer.timeout.connect(self.volume_popup.hide)

        # 静音
        self.btn_volume.clicked.connect(self.toggle_mute)

    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.btn_play.setText("▶️")
        else:
            self.media_player.play()
            self.btn_play.setText("⏸️")

    def toggle_mute(self):
        if self.audio_output.isMuted():
            self.audio_output.setMuted(False)
            self.update_volume(self.volume_popup.slider.value())
        else:
            self.audio_output.setMuted(True)
            self.btn_volume.setText("🔇")

    def sync_slider_position(self, position):
        # 更新滑块位置
        self.slider_progress.setValue(position)
        # 更新时间标签 (ms -> mm:ss)
        curr = self.format_time(position)
        total = self.format_time(self.media_player.duration())
        self.lbl_time.setText(f"{curr} / {total}")

    def sync_slider_range(self, duration):
        self.slider_progress.setRange(0, duration)

    def seek_position(self, position):
        self.media_player.setPosition(position)

    def on_play_finished(self, status):
        if status ==QMediaPlayer.MediaStatus.EndOfMedia:
            self.btn_play.setText("▶️")

    def show_volume_popup(self):
        self.volume_popup.adjustSize()

        # 获取按钮中心在全球屏幕中的坐标
        btn_global_pos = self.btn_volume.mapToGlobal(QPoint(0, 0))

        px = btn_global_pos.x() + (self.btn_volume.width() // 2) - (self.volume_popup.width() // 2)
        py = btn_global_pos.y() - self.volume_popup.height() + 2

        self.volume_popup.move(px, py)
        self.volume_popup.show()

    def update_volume(self, value):
        volume_float = value / 100.0
        self.audio_output.setVolume(volume_float)
        if self.audio_output.isMuted():
            self.btn_volume.setText("🔇")
            return
        if value == 0:
            self.btn_volume.setText("🔇")
        elif value < 50:
            self.btn_volume.setText("🔉")
        else:
            self.btn_volume.setText("🔊")

    @staticmethod
    def format_time(ms):
        s = ms // 1000
        m, s = divmod(s, 60)
        return f"{m:02d}:{s:02d}"
