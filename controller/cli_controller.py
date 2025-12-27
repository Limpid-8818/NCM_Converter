import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional

from domain.exceptions import NCMException
from domain.models import NCMMetadata
from session.decryption_session import DecryptionSession


class CLIPresenter:
    @staticmethod
    def display_metadata(metadata: NCMMetadata) -> None:
        artist_str = ', '.join(metadata.artist)
        duration_str = f"{metadata.duration // 60000}分{ metadata.duration % 60000 // 1000}秒"

        print("歌曲元数据解析成功：")
        print(f"  歌曲名：{metadata.title}")
        print(f"  歌手：{artist_str}")
        print(f"  专辑：{metadata.album}")
        print(f"  格式：{metadata.format}")
        print(f"  时长：{duration_str}")

    @staticmethod
    def display_error(msg: str) -> None:
        print(f"错误: {msg}", file=sys.stderr)

    @staticmethod
    def display_progress(current: int, total: int, msg: str) -> None:
        percent = (current / total) * 100 if total > 0 else 0
        bar_length = 50
        filled_length = int(bar_length * percent // 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        sys.stdout.write(f"\r[{bar}] {percent:5.1f}% | {msg}")
        sys.stdout.flush()

        if "完成" in msg:
            print()


class CLIArgParser:
    def __init__(self):
        self._parser = ArgumentParser(
            prog="ncm-converter-cli",
            description="NetEase Cloud Music Encrypted File Converter Command Line Tool\n"
                        "网易云音乐加密格式文件转换工具"
        )
        self._setup_arguments()

    def _setup_arguments(self):
        self._parser.add_argument(
            "input_file",
            type=str,
            help="Input file path\t输入文件路径"
        )
        self._parser.add_argument(
            "-p", "--preview",
            action="store_true",
            help="Preview mode\t仅预览文件信息，不解密导出"
        )
        self._parser.add_argument(
            "-o", "--output",
            type=str,
            help="Output file path\t输出文件路径（可选，默认同级目录）"
        )

    def parse(self) -> Namespace:
        return self._parser.parse_args()


class CLIController:
    def __init__(self):
        self._parser = CLIArgParser()
        self._presenter = CLIPresenter()
        self._args: Optional[Namespace] = self._parser.parse()

    def _execute(self):
        file_path_str = self._args.input_file
        file_path = Path(file_path_str).resolve()
        print(f"Input File: {file_path}")

        session = DecryptionSession(str(file_path))
        metadata = session.get_metadata()
        self._presenter.display_metadata(metadata)

        if self._args.preview:
            return

        print("正在解码...")
        output_path = self._get_output_path(metadata.format)
        session.export_with_chunk(str(output_path), progress_callback=self._presenter.display_progress)
        print(f"导出成功，Output File: {output_path}")

    def _get_output_path(self, audio_format: str) -> Path:
        if self._args.output:
            return Path(self._args.output).resolve()

        input_path = Path(self._args.input_file).resolve()
        output_name = input_path.stem + "." + audio_format
        return input_path.parent / output_name

    def run(self) -> bool:
        try:
            self._execute()
            return True
        except KeyboardInterrupt:
            print("\n\nInterrupted by user  任务中止")
            return True
        except NCMException as e:
            self._presenter.display_error(str(e))
            return False
        except Exception as e:
            self._presenter.display_error(str(e))
            return False
