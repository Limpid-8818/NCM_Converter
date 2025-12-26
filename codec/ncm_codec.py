import base64
import binascii
import json
from json import JSONDecodeError
from typing import BinaryIO

from Crypto.Cipher import AES


class NCMCodec:
    AUDIO_KEY_HEX = "687A4852416D736F356B496E62617857"
    METADATA_KEY_HEX = "2331346C6A6B5F215C5D2630553C2728"
    AUDIO_KEY = bytes.fromhex(AUDIO_KEY_HEX)
    METADATA_KEY = bytes.fromhex(METADATA_KEY_HEX)

    NCM_HEADER = b"CTENFDAM"  # NCM文件头（8字节）
    AUDIO_KEY_PREFIX = b"neteasecloudmusic"  # 音频密钥明文前缀（17字节）
    METADATA_PREFIX = b"163 key(Don't modify):"  # 元数据明文前缀（22字节）
    AUDIO_XOR_VALUE = 0x64  # 音频密钥密文异或值
    METADATA_XOR_VALUE = 0x63  # 元数据密文异或值

    def __init__(self):
        pass

    @classmethod
    def validate_file(cls, file_stream: BinaryIO) -> bool:
        """
        Check if a file is valid.
        检查文件是否可以正常读取。

        :param file_stream: BinaryIO
        :return: boolean
        """
        if not file_stream:
            return False

        try:
            original_offset = file_stream.tell()
            file_stream.read(1)
            file_stream.seek(original_offset)
            return True

        except (IOError, OSError, ValueError):
            return False

    @classmethod
    def verify_format(cls, header_bytes: bytes) -> bool:
        """
        Check if a file is NCM format. True -> .ncm; False -> .flac.
        检查文件是否为NCM格式。是则返回真，不是则为FLAC格式，返回假。

        :param header_bytes: bytes
        :return: boolean
        """
        if len(header_bytes) != 8:
            return False
        return header_bytes == cls.NCM_HEADER

    @classmethod
    def derive_key(cls, key_related_bytes: bytes) -> bytes:
        """
        Derive the RC4 key for audio from file stream.
        从文件中获取音频RC4密钥。

        :param key_related_bytes: bytes 包含密钥长度和加密密钥的字节（至少132字节：4+128）
        :return: bytes RC4音频密钥
        :raise: ValueError
        """
        if len(key_related_bytes) < 132:
            raise ValueError("Key related bytes length is less than 132")

        try:
            key_length_bytes = key_related_bytes[:4]
            key_length = int.from_bytes(key_length_bytes, byteorder="little")
            if key_length != 128:
                raise ValueError("Key length is not 128")

            encrypted_key = key_related_bytes[4:4 + key_length]

            aes_cipher_text = bytes([b ^ cls.AUDIO_XOR_VALUE for b in encrypted_key])
            decrypted_raw = AES.new(cls.AUDIO_KEY, mode=AES.MODE_ECB).decrypt(aes_cipher_text)

            prefix_length = len(cls.AUDIO_KEY_PREFIX)
            if not decrypted_raw.startswith(cls.AUDIO_KEY_PREFIX):
                raise ValueError("Metadata prefix is not correct")

            key_with_padding = decrypted_raw[prefix_length:]
            if not key_with_padding:
                raise ValueError("Empty key")
            padding_length = key_with_padding[-1]
            if padding_length <= 0 or padding_length > 16:
                raise ValueError("Invalid PKCS7 padding length")

            rc4_key = key_with_padding[:-padding_length]
            return rc4_key

        except Exception as e:
            raise ValueError("Derive RC4 key failed：{}".format(str(e)))

    @classmethod
    def decrypt_metadata(cls, encrypted_metadata: bytes) -> dict:
        """
        Decrypt metadata for NCM.
        解密文件元数据，返回JSON元数据字典。

        :param encrypted_metadata: bytes 加密JSON元数据
        :return: dict 解析后的元数据字典
        """
        if not encrypted_metadata:
            raise ValueError("Empty metadata")

        try:
            metadata_cipher_with_prefix = bytes([b ^ cls.METADATA_XOR_VALUE for b in encrypted_metadata])

            prefix_length = len(cls.METADATA_PREFIX)
            if len(metadata_cipher_with_prefix) < prefix_length:
                raise ValueError("Invalid metadata")
            if not metadata_cipher_with_prefix.startswith(cls.METADATA_PREFIX):
                raise ValueError("Metadata prefix is not correct")
            metadata_b64_cipher = metadata_cipher_with_prefix[prefix_length:]

            try:
                metadata_aes_cipher = base64.b64decode(metadata_b64_cipher)
            except binascii.Error as e:
                raise ValueError(f"Decode base64 error: {e}")

            decrypted_raw = AES.new(cls.METADATA_KEY, mode=AES.MODE_ECB).decrypt(metadata_aes_cipher)

            if not decrypted_raw:
                raise ValueError("Empty metadata")
            padding_length = decrypted_raw[-1]
            if padding_length <= 0 or padding_length > 16:
                raise ValueError("Invalid PKCS7 padding length")

            metadata_json_bytes = decrypted_raw[:-padding_length]

            try:
                metadata_json = metadata_json_bytes.decode("utf-8")
                if "music:" in metadata_json:
                    metadata_json = metadata_json.split("music:", 1)[1]
                metadata_dict = json.loads(metadata_json)
            except UnicodeDecodeError as e:
                raise ValueError(f"Decode UTF-8 error: {e}")
            except JSONDecodeError as e:
                raise ValueError(f"Decode JSON error: {e}")

            return metadata_dict

        except Exception as e:
            raise ValueError(f"Decode JSON error: {str(e)}")

    @staticmethod
    def decrypt_audio(encrypted_audio: bytes, rc4_key: bytes) -> bytes:
        """
        Decrypt audio for NCM.
        解密音频数据流。

        :param encrypted_audio: bytes
        :param rc4_key: bytes
        :return: bytes
        """
        if not rc4_key:
            raise ValueError("Empty rc4 key")
        if not encrypted_audio:
            raise ValueError("Empty audio")

        try:
            s_box = bytearray(range(256))
            key_length = len(rc4_key)

            j = 0
            for i in range(256):
                j = (j + s_box[i] + rc4_key[i % key_length]) & 0xFF
                s_box[i], s_box[j] = s_box[j], s_box[i]

            output = bytearray()
            i, j = 0, 0
            for byte in encrypted_audio:
                i = (i + 1) & 0xff
                j = (i + s_box[i]) & 0xff
                k = s_box[(s_box[i] + s_box[j]) & 0xff]
                output.append(byte ^ k)

            return bytes(output)

        except Exception as e:
            raise ValueError("Decrypt audio failed: {}".format(str(e)))
