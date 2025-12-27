from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class NCMMetadata:
    music_id: str
    title: str
    artist: List[str]
    artist_ids: List[Optional[int]]
    album: str
    album_id: str
    format: str
    duration: int
    bitrate: int

    @classmethod
    def load_from_dict(cls, data: Dict[str, Any]) -> NCMMetadata:
        return cls(
            music_id=data.get("music_id", ""),
            title=data.get("musicName", "未知歌曲"),
            artist=[artist[0] for artist in data.get('artist', [])],
            artist_ids=[artist[1] if artist[1] else None for artist in data.get('artist', [])],
            album=data.get("album", "未知专辑"),
            album_id=data.get("albumId", ""),
            format=data.get("format", "flac"),
            duration=data.get("duration", 0),
            bitrate=data.get("bitrate", 0)
        )

