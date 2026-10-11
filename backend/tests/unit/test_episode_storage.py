from botocore.exceptions import ClientError

import pytest

from services.episode_storage import (
    AudioStorageError,
    S3EpisodeStorage,
    get_episode_storage,
    stored_audio_exists,
)


class _Body:
    def __init__(self, data: bytes):
        self._data = data
        self.closed = False

    def read(self, size: int) -> bytes:
        block = self._data[:size]
        self._data = self._data[size:]
        return block

    def close(self) -> None:
        self.closed = True


class _Bucket:
    def __init__(self):
        self.objects = {}
        self.calls = []

    def put_object(self, **kwargs):
        self.calls.append(("put", kwargs["Key"]))
        self.objects[kwargs["Key"]] = kwargs["Body"]
        assert kwargs["ContentType"] == "audio/wav"
        assert kwargs["Bucket"] == "episodes"

    def get_object(self, **kwargs):
        self.calls.append(("get", kwargs["Key"]))
        data = self.objects.get(kwargs["Key"])
        if data is None:
            raise _missing("GetObject")
        return {"Body": _Body(data)}

    def delete_object(self, **kwargs):
        self.calls.append(("delete", kwargs["Key"]))
        self.objects.pop(kwargs["Key"], None)

    def head_object(self, **kwargs):
        self.calls.append(("head", kwargs["Key"]))
        if kwargs["Key"] not in self.objects:
            raise _missing("HeadObject")


def _missing(operation: str) -> ClientError:
    return ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "missing"}},
        operation,
    )


def _storage(bucket: _Bucket) -> S3EpisodeStorage:
    return S3EpisodeStorage(
        bucket="episodes",
        access_key="key",
        secret_key="secret",
        endpoint_url="https://example.r2.cloudflarestorage.com",
        region="auto",
        client=bucket,
    )


def test_s3_storage_round_trips_and_replaces_an_object():
    bucket = _Bucket()
    storage = _storage(bucket)
    payload = b"a" * (70 * 1024)

    storage.put("episodes/4.wav", payload)
    assert storage.exists("episodes/4.wav") is True
    assert b"".join(storage.stream("episodes/4.wav")) == payload

    storage.put("episodes/4.wav", b"next")
    assert b"".join(storage.stream("episodes/4.wav")) == b"next"
    storage.delete("episodes/4.wav")
    storage.delete("episodes/4.wav")
    assert storage.exists("episodes/4.wav") is False
    with pytest.raises(FileNotFoundError):
        b"".join(storage.stream("episodes/4.wav"))
    assert bucket.calls[0] == ("put", "episodes/4.wav")


def test_s3_storage_rejects_a_key_that_escapes_the_bucket():
    bucket = _Bucket()
    storage = _storage(bucket)
    with pytest.raises(AudioStorageError):
        storage.put("../secret.wav", b"nope")
    assert bucket.calls == []


def test_s3_storage_is_selected_from_the_environment(monkeypatch):
    monkeypatch.setenv("EPISODE_STORAGE", "s3")
    monkeypatch.setenv("EPISODE_S3_BUCKET", "episodes")
    monkeypatch.setenv("EPISODE_S3_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("EPISODE_S3_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv(
        "EPISODE_S3_ENDPOINT_URL", "https://example.r2.cloudflarestorage.com"
    )
    monkeypatch.setenv("EPISODE_S3_REGION", "auto")
    created = {}

    def fake_client(**kwargs):
        created.update(kwargs)
        return object()

    monkeypatch.setattr("boto3.client", fake_client)
    storage = get_episode_storage()
    assert isinstance(storage, S3EpisodeStorage)
    assert storage.client is not None
    assert created["endpoint_url"] == "https://example.r2.cloudflarestorage.com"
    assert created["region_name"] == "auto"
    assert created["aws_access_key_id"] == "key"


def test_local_storage_stays_selected_when_forced(monkeypatch, tmp_path):
    monkeypatch.setenv("EPISODE_STORAGE", "local")
    monkeypatch.setenv("EPISODE_MEDIA_DIR", str(tmp_path))
    monkeypatch.setenv("EPISODE_S3_BUCKET", "episodes")
    monkeypatch.setenv("EPISODE_S3_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("EPISODE_S3_SECRET_ACCESS_KEY", "secret")
    storage = get_episode_storage()
    storage.put("episodes/1.wav", b"local")
    assert (tmp_path / "episodes" / "1.wav").read_bytes() == b"local"


def test_s3_mode_without_credentials_fails(monkeypatch):
    monkeypatch.setenv("EPISODE_STORAGE", "s3")
    monkeypatch.delenv("EPISODE_S3_BUCKET", raising=False)
    monkeypatch.delenv("EPISODE_S3_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("EPISODE_S3_SECRET_ACCESS_KEY", raising=False)
    with pytest.raises(AudioStorageError, match="EPISODE_S3_BUCKET"):
        get_episode_storage()


def test_a_storage_outage_does_not_look_like_a_missing_file(monkeypatch):
    class Down:
        def exists(self, key):
            raise AudioStorageError("bucket unavailable")

    monkeypatch.setattr(
        "services.episode_storage.get_episode_storage", lambda: Down()
    )
    assert stored_audio_exists("episodes/4.wav") is True
    assert stored_audio_exists("jobs/claim") is False
