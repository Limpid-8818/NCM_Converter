from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal, QObject, Slot, QTimer

from domain.exceptions import NCMException
from domain.models import NCMMetadata
from session.decryption_session import DecryptionSession


class DecryptWorker(QThread):
    signal_progress_updated = Signal(int, int, str)  # 解码处理进度信号：当前进度，总进度，消息
    signal_task_finished = Signal(bool, NCMMetadata, bytes, str)  # 任务完成信号：是否为预览，元数据，封面，导出地址
    signal_error_occurred = Signal(str)  # 错误信号：错误消息

    def __init__(self, session: DecryptionSession, output_file: Optional[str] = None, preview_only: bool = False):
        super().__init__()
        self.session = session
        self.output_file = output_file
        self.preview_only = preview_only

    def run(self):
        try:
            self.session.preview()
            metadata = self.session.get_metadata()
            cover_bytes = self.session.get_cover_bytes()

            if self.preview_only:
                self.signal_task_finished.emit(True, metadata, cover_bytes, "")
                return

            self.output_file = self._get_path(metadata.format)

            self.signal_progress_updated.emit(0, 100, "正在准备音频解码...")

            def progress_cb(current, total, msg):
                percent = int(current * 100 / total)
                self.signal_progress_updated.emit(min(percent, 100), 100, msg)

            self.session.export_with_chunk(self.output_file, progress_callback=progress_cb)
            self.signal_progress_updated.emit(100, 100, "解码完成")

            self.signal_task_finished.emit(False, metadata, cover_bytes, self.output_file)

        except NCMException as e:
            self.signal_error_occurred.emit(str(e))
        except Exception as e:
            self.signal_error_occurred.emit(str(e))

    def _get_path(self, audio_format: str) -> str:
        input_path = Path(self.session.file_path)
        if not self.output_file:
            return str(input_path.parent / (input_path.stem + "." + audio_format))

        output_path = Path(self.output_file).resolve()
        if output_path.is_dir():
            return str(output_path / (input_path.stem + "." + audio_format))
        else:
            return self.output_file


class GUIController(QObject):
    signal_update_progress = Signal(int, int, str)
    signal_update_metadata = Signal(NCMMetadata)
    signal_update_cover_bytes = Signal(bytes)
    signal_show_message = Signal(str, str)
    signal_set_export_btn_enabled = Signal(bool)
    signal_decryption_finished = Signal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        self.current_session: Optional[DecryptionSession] = None
        self.input_file: Optional[Path] = None
        self.output_file: Optional[Path] = None
        self.decrypt_worker: Optional[DecryptWorker] = None

        self.batch_mode = False

    def set_input_file(self, file_path: str):
        if not file_path or not Path(file_path).resolve().exists():
            self.signal_show_message.emit("info", "文件不存在，请重新选择！")
            return

        self.input_file = Path(file_path).resolve()
        self.current_session = DecryptionSession(str(self.input_file))
        self.start_preview()
        self.signal_set_export_btn_enabled.emit(True)

    def set_output_file(self, file_path: Optional[str] = None):
        self.output_file = Path(file_path).resolve() if file_path else None

    def start_preview(self):
        if not self.current_session:
            self.signal_show_message.emit("info", "请先选择 NCM 文件！")
            return

        self._stop_worker()

        self.decrypt_worker = DecryptWorker(
            session=self.current_session,
            preview_only=True,
        )

        self._bind_worker_signals()

        self.decrypt_worker.start()

    def start_decrypt(self):
        if not self.current_session:
            self.signal_show_message.emit("info", "请先选择 NCM 文件！")
            return

        self._stop_worker()

        self.decrypt_worker = DecryptWorker(
            session=self.current_session,
            output_file=self.output_file,
            preview_only=False,
        )

        self._bind_worker_signals()

        self.decrypt_worker.start()

    def _bind_worker_signals(self):
        if not self.decrypt_worker:
            return

        self.decrypt_worker.signal_progress_updated.connect(self._on_worker_progress)
        self.decrypt_worker.signal_task_finished.connect(self._on_worker_task_finished)
        self.decrypt_worker.signal_error_occurred.connect(self._on_worker_error)

    def _stop_worker(self):
        if self.decrypt_worker and self.decrypt_worker.isRunning():
            self.decrypt_worker.terminate()
            self.decrypt_worker.wait()
        self.decrypt_worker = None

    @Slot(int, int, str)
    def _on_worker_progress(self, current, total, msg):
        self.signal_update_progress.emit(current, total, msg)

    @Slot(bool, NCMMetadata, bytes, str)
    def _on_worker_task_finished(self, preview_only, metadata, cover_bytes, path):
        self.signal_update_metadata.emit(metadata)
        self.signal_update_cover_bytes.emit(cover_bytes)
        if preview_only:
            self.signal_show_message.emit("info", "元数据与封面预览完成")
        else:
            self.signal_show_message.emit("info", f"音频解码成功\n保存路径：{path}")
            QTimer.singleShot(200, lambda: self.signal_decryption_finished.emit(path))

    @Slot(str)
    def _on_worker_error(self, msg):
        self.signal_show_message.emit("error", f"操作失败：{msg}")
        self.signal_update_progress.emit(0, 100, "就绪")
