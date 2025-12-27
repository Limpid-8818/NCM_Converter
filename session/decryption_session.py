import os
from pathlib import Path
from typing import Optional, Callable

from codec.ncm_codec import NCMCodec
from domain.exceptions import NCMFileValidationException, NCMExportException
from domain.models import NCMMetadata

"""
进度回调类型注解：目前进度，总进度，状态信息
"""
ProgressCallback = Callable[[int, int, str], None]

class DecryptionSession:
    def __init__(self, ncm_file_path: str):
        self.file_path_str: str = ncm_file_path
        self.file_path: Path = Path(ncm_file_path).resolve()
        self.file_size: int = os.path.getsize(self.file_path)

        self._rc4_key: Optional[bytes] = None
        self._metadata: Optional[NCMMetadata] = None
        self._cover_bytes: Optional[bytes] = None
        self._rc4_key_offset: int = 10
        self._metadata_offset: int = 142
        self._cover_offset: Optional[int] = None
        self._audio_offset: Optional[int] = None
        self._audio_size: Optional[int] = None

        self._pre_check()

    def _pre_check(self):
        if not os.path.isfile(self.file_path):
            raise NCMFileValidationException(f"目标文件不存在：{self.file_path}")

        try:
            with open(self.file_path, "rb") as f:
                if not NCMCodec.validate_file(f):
                    raise IOError(f"目标文件不可读：{self.file_path}")
        except (IOError, OSError) as e:
            raise NCMFileValidationException(str(e))

        with open(self.file_path, "rb") as f:
            header_bytes = f.read(8)
            if not NCMCodec.verify_format(header_bytes):
                raise NCMFileValidationException(f"文件不是合法的NCM格式：{self.file_path}")

    def _extract_key(self):
        if self._rc4_key is not None:
            return

        with open(self.file_path, "rb") as f:
            f.seek(self._rc4_key_offset)
            key_related_bytes = f.read(132)

            self._rc4_key = NCMCodec.derive_key(key_related_bytes)

    def _extract_metadata(self):
        if self._metadata is not None:
            return

        with open(self.file_path, "rb") as f:
            f.seek(self._metadata_offset)
            metadata_length_bytes = f.read(4)
            metadata_length = int.from_bytes(metadata_length_bytes, byteorder='little')

            encrypted_metadata_bytes = f.read(metadata_length)

            metadata_dic = NCMCodec.decrypt_metadata(encrypted_metadata_bytes)
            metadata = NCMMetadata.load_from_dict(metadata_dic)
            self._metadata = metadata

            self._cover_offset = self._metadata_offset + 4 + metadata_length

    def _extract_cover(self):
        if self._cover_bytes is not None:
            return

        if self._cover_offset is None:
            self._extract_metadata()

        with open(self.file_path, "rb") as f:
            f.seek(self._cover_offset)
            f.read(9)

            cover_length_bytes = f.read(4)
            cover_length = int.from_bytes(cover_length_bytes, byteorder='little')

            self._cover_bytes = f.read(cover_length)

            self._audio_offset = f.tell()
            self._audio_size = self.file_size - self._audio_offset

    def preview(self):
        self._extract_metadata()
        self._extract_cover()

    def decrypt(self) -> bytes:
        if self._audio_offset is None:
            self.preview()

        if self._rc4_key is None:
            self._extract_key()

        with open(self.file_path, "rb") as f:
            f.seek(self._audio_offset)
            encrypted_audio_bytes = f.read()

            decrypted_audio_bytes = NCMCodec.decrypt_audio(encrypted_audio_bytes, self._rc4_key)

        return decrypted_audio_bytes

    def decrypt_with_chunk(self, chunk_size: int = 1024 * 1024,
                           progress_callback: Optional[ProgressCallback] = None) -> Optional[bytes]:
        if self._audio_offset is None:
            self.preview()

        if self._rc4_key is None:
            self._extract_key()

        decrypted_audio = bytearray()
        processed_size = 0
        total_size = self._audio_size

        with open(self.file_path, "rb") as f:
            f.seek(self._audio_offset)

            if progress_callback:
                progress_callback(processed_size, total_size, "开始任务")

            while True:
                encrypted_chunk = f.read(chunk_size)
                if not encrypted_chunk:
                    break

                decrypted_chunk = NCMCodec.decrypt_audio(encrypted_chunk, self._rc4_key)
                decrypted_audio.extend(decrypted_chunk)

                processed_size += len(decrypted_chunk)

                if progress_callback:
                    current = min(processed_size, total_size)
                    progress_callback(current, total_size,
                                      f"已处理 {current/1024/1024:.2f}MB / {total_size/1024/1024:.2f}MB")

            if progress_callback:
                progress_callback(total_size, total_size, "任务完成")

            return bytes(decrypted_audio)

    def export(self, output_path: str):
        decrypted_audio_bytes = self.decrypt()

        try:
            with open(output_path, "wb") as f:
                f.write(decrypted_audio_bytes)
        except (IOError, OSError) as e:
            raise NCMExportException(f"导出音频失败：{str(e)}")

    def export_with_chunk(self, output_path: str,
                          chunk_size: int = 1024 * 1024,
                          progress_callback: Optional[ProgressCallback] = None):
        decrypted_audio_bytes = self.decrypt_with_chunk(chunk_size, progress_callback)

        try:
            with open(output_path, "wb") as f:
                f.write(decrypted_audio_bytes)
        except (IOError, OSError) as e:
            raise NCMExportException(f"导出音频失败：{str(e)}")

    def get_metadata(self) -> NCMMetadata:
        if self._metadata is None:
            self.preview()
        return self._metadata

    def get_cover_bytes(self) -> bytes:
        if self._cover_offset is None:
            self.preview()
        return self._cover_bytes


if __name__ == "__main__":
    file_path = "test.ncm"
    session = DecryptionSession(file_path)

    session.preview()
    print(session.get_metadata())

    output_path = "test.mp3"
    session.export(output_path)

    def print_progress(current, total, msg):
        print(msg)

    session.decrypt_with_chunk(progress_callback=print_progress)