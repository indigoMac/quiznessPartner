"""Store episode audio outside the database.

The database keeps an object key. Local development writes that key under
EPISODE_MEDIA_DIR. Production writes the same key to an S3-compatible bucket
when EPISODE_S3_BUCKET and its credentials are set.
"""

import logging
import os
from pathlib import Path
from typing import Iterator, Optional, Protocol

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

_CHUNK_BYTES = 64 * 1024
_MISSING_CODES = {"NoSuchKey", "404", "NotFound", "NoSuchBucket"}


class AudioStorageError(Exception):
    """Raised when an audio key cannot be mapped to stored bytes."""


class EpisodeStorage(Protocol):
    def put(self, key: str, data: bytes) -> None:
        """Write the object, replacing any bytes already stored at key."""

    def stream(self, key: str) -> Iterator[bytes]:
        """Yield the object in order. Raise FileNotFoundError when missing."""

    def delete(self, key: str) -> None:
        """Remove the object. Missing objects are not an error."""

    def exists(self, key: str) -> bool:
        """True when the object is stored at key."""


def validate_audio_key(key: str) -> None:
    parts = Path(key).parts
    if (
        not key
        or key.startswith(("/", "\\"))
        or "\\" in key
        or ".." in parts
        or any(part in ("", ".", "..") for part in parts)
    ):
        raise AudioStorageError("Invalid episode audio key.")


def _is_missing(exc: ClientError) -> bool:
    code = exc.response.get("Error", {}).get("Code", "")
    return code in _MISSING_CODES


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

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def _path(self, key: str) -> Path:
        validate_audio_key(key)
        root = self.root.resolve()
        path = (root / key).resolve()
        if path != root and root not in path.parents:
            raise AudioStorageError("Invalid episode audio key.")
        return path


class S3EpisodeStorage:
    """Write audio objects to an S3-compatible bucket, including Cloudflare R2."""

    def __init__(
        self,
        bucket: str,
        access_key: str,
        secret_key: str,
        endpoint_url: Optional[str] = None,
        region: str = "auto",
        client=None,
    ):
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url or None
        self.region = region or "auto"
        self._client = client

    @classmethod
    def from_env(cls) -> "S3EpisodeStorage":
        bucket = os.getenv("EPISODE_S3_BUCKET", "").strip()
        access_key = os.getenv("EPISODE_S3_ACCESS_KEY_ID", "").strip()
        secret_key = os.getenv("EPISODE_S3_SECRET_ACCESS_KEY", "").strip()
        if not bucket or not access_key or not secret_key:
            raise AudioStorageError(
                "Episode object storage is not configured. Set EPISODE_S3_BUCKET, "
                "EPISODE_S3_ACCESS_KEY_ID, and EPISODE_S3_SECRET_ACCESS_KEY."
            )
        return cls(
            bucket=bucket,
            access_key=access_key,
            secret_key=secret_key,
            endpoint_url=os.getenv("EPISODE_S3_ENDPOINT_URL", "").strip() or None,
            region=os.getenv("EPISODE_S3_REGION", "auto").strip() or "auto",
        )

    @property
    def client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client(
                service_name="s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
            )
        return self._client

    def put(self, key: str, data: bytes) -> None:
        validate_audio_key(key)
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType="audio/wav",
            )
        except ClientError as exc:
            raise AudioStorageError("Could not store the episode audio.") from exc

    def stream(self, key: str) -> Iterator[bytes]:
        validate_audio_key(key)
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            if _is_missing(exc):
                raise FileNotFoundError(key) from exc
            raise AudioStorageError("Could not read the episode audio.") from exc
        body = response["Body"]

        def chunks() -> Iterator[bytes]:
            try:
                while True:
                    block = body.read(_CHUNK_BYTES)
                    if not block:
                        break
                    yield block
            finally:
                body.close()

        return chunks()

    def delete(self, key: str) -> None:
        validate_audio_key(key)
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            if _is_missing(exc):
                return
            raise AudioStorageError("Could not delete the episode audio.") from exc

    def exists(self, key: str) -> bool:
        validate_audio_key(key)
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            if _is_missing(exc):
                return False
            raise AudioStorageError("Could not check the episode audio.") from exc
        return True


def episode_media_dir() -> Path:
    return Path(os.getenv("EPISODE_MEDIA_DIR", "var/episode-media"))


def _s3_settings_present() -> bool:
    return bool(
        os.getenv("EPISODE_S3_BUCKET", "").strip()
        and os.getenv("EPISODE_S3_ACCESS_KEY_ID", "").strip()
        and os.getenv("EPISODE_S3_SECRET_ACCESS_KEY", "").strip()
    )


def get_episode_storage() -> EpisodeStorage:
    mode = os.getenv("EPISODE_STORAGE", "auto").strip().lower() or "auto"
    if mode == "local":
        return LocalEpisodeStorage(episode_media_dir())
    if mode == "s3" or (mode == "auto" and _s3_settings_present()):
        return S3EpisodeStorage.from_env()
    if mode != "auto":
        raise AudioStorageError("EPISODE_STORAGE must be auto, local, or s3.")
    return LocalEpisodeStorage(episode_media_dir())


def stored_audio_exists(key: Optional[str]) -> bool:
    """True when a finished audio object is still stored.

    A storage outage reports the object as present so a retry does not spend
    another speech job while the bucket cannot be reached.
    """
    if not key or not key.startswith("episodes/"):
        return False
    try:
        return get_episode_storage().exists(key)
    except (OSError, AudioStorageError):
        logger.warning("Could not check episode audio %s", key, exc_info=True)
        return True


def delete_stored_audio(key: Optional[str]) -> None:
    """Remove a finished audio object. Claim tokens are not files."""
    if not key or not key.startswith("episodes/"):
        return
    try:
        get_episode_storage().delete(key)
    except (OSError, AudioStorageError):
        logger.warning("Could not delete episode audio %s", key, exc_info=True)
