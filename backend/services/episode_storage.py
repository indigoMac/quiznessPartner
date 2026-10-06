"""Store episode audio outside the database.

The database keeps an object key. This local directory is the development
implementation. Swap it for object storage before production.
"""

import logging
import os
from pathlib import Path
from typing import Iterator, Optional, Protocol

logger = logging.getLogger(__name__)

_CHUNK_BYTES = 64 * 1024


class AudioStorageError(Exception):
    """Raised when an audio key cannot be mapped to stored bytes."""


class EpisodeStorage(Protocol):
    def put(self, key: str, data: bytes) -> None:
        """Write the object, replacing any bytes already stored at key."""

    def stream(self, key: str) -> Iterator[bytes]:
        """Yield the object in order. Raise FileNotFoundError when missing."""

    def delete(self, key: str) -> None:
        """Remove the object. Missing objects are not an error."""


class LocalEpisodeStorage:
    """Write audio files under EPISODE_MEDIA_DIR."""

    def __init__(self, root: Path):
        self.root = root

    def put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def stream(self, key: str) -> Iterator[bytes]:
        path = self._path(key)
        if not path.is_file():
            raise FileNotFoundError(key)

        def chunks() -> Iterator[bytes]:
            with path.open("rb") as handle:
                while True:
                    block = handle.read(_CHUNK_BYTES)
                    if not block:
                        break
                    yield block

        return chunks()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.is_file():
            path.unlink()

    def _path(self, key: str) -> Path:
        parts = Path(key).parts
        if not key or key.startswith(("/", "\\")) or ".." in parts:
            raise AudioStorageError("Invalid episode audio key.")
        root = self.root.resolve()
        path = (root / key).resolve()
        if path != root and root not in path.parents:
            raise AudioStorageError("Invalid episode audio key.")
        return path


def episode_media_dir() -> Path:
    return Path(os.getenv("EPISODE_MEDIA_DIR", "var/episode-media"))


def get_episode_storage() -> EpisodeStorage:
    return LocalEpisodeStorage(episode_media_dir())


def delete_stored_audio(key: Optional[str]) -> None:
    """Remove a finished audio object. Claim tokens are not files."""
    if not key or not key.startswith("episodes/"):
        return
    try:
        get_episode_storage().delete(key)
    except (OSError, AudioStorageError):
        logger.warning("Could not delete episode audio %s", key, exc_info=True)
