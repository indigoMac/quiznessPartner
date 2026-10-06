import io
import struct
import wave
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from models.episode import AUDIO_GENERATING, AUDIO_READY
from services.episode_audio import (
    AudioSynthesisError,
    _provider_message,
    audio_generation_in_progress,
    concatenate_wavs,
    render_episode_audio,
    split_for_speech,
    synthesize_speech,
    timings_from_durations,
    wav_duration_seconds,
)
from services.episode_storage import AudioStorageError, LocalEpisodeStorage


def _silence_wav(seconds: float, rate: int = 8000) -> bytes:
    frames = int(seconds * rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b"\x00\x00" * frames)
    return buffer.getvalue()


def test_timings_from_durations_places_each_segment_after_the_previous():
    timings = timings_from_durations([1.5, 2.0, 0.5])
    assert timings == [
        {"start": 0.0, "end": 1.5},
        {"start": 1.5, "end": 3.5},
        {"start": 3.5, "end": 4.0},
    ]


def test_timings_reject_a_segment_with_no_audio():
    with pytest.raises(AudioSynthesisError):
        timings_from_durations([1.0, 0.0])


def test_split_for_speech_keeps_words_within_the_provider_limit():
    text = " ".join(["mitochondria"] * 30)
    parts = split_for_speech(text)
    assert len(parts) > 1
    assert all(len(part) <= 200 for part in parts)
    assert " ".join(parts) == text


def test_split_for_speech_cuts_a_word_longer_than_the_limit():
    parts = split_for_speech("a" * 450)
    assert parts == ["a" * 200, "a" * 200, "a" * 50]


def test_split_for_speech_rejects_blank_text():
    with pytest.raises(AudioSynthesisError):
        split_for_speech("   ")


def test_render_episode_audio_times_each_script_segment(monkeypatch):
    calls = []

    def fake_speech(text, voice):
        calls.append((text, voice))
        assert len(text) <= 200
        return _silence_wav(0.5)

    monkeypatch.setattr("services.episode_audio.synthesize_speech", fake_speech)
    script = [
        {"chapter": "Cells", "speaker": "host_a", "text": "mitochondria " * 40},
        {"chapter": "Cells", "speaker": "host_b", "text": "They make energy."},
    ]

    audio, timings = render_episode_audio(script)

    assert len(calls) > 2
    assert {voice for _text, voice in calls} == {"autumn", "austin"}
    assert calls[-1] == ("They make energy.", "austin")
    assert len(timings) == 2
    assert timings[0]["start"] == 0.0
    assert timings[1]["start"] == timings[0]["end"]
    assert wav_duration_seconds(audio) == pytest.approx(timings[-1]["end"])


def test_concatenate_wavs_keeps_the_sum_of_durations():
    combined = concatenate_wavs([_silence_wav(1.0), _silence_wav(0.5)])
    assert wav_duration_seconds(combined) == pytest.approx(1.5)


def _wav_with_placeholder_frame_count(pcm: bytes, rate: int = 8000) -> bytes:
    """A WAV whose header claims 0xFFFFFFFF data bytes, like some speech APIs."""
    channels = 1
    width = 2
    return struct.pack(
        "<4sL4s4sLHHLLHH4sL",
        b"RIFF",
        0xFFFFFFFF,
        b"WAVE",
        b"fmt ",
        16,
        1,
        channels,
        rate,
        channels * rate * width,
        channels * width,
        width * 8,
        b"data",
        0xFFFFFFFF,
    ) + pcm


def test_concatenate_wavs_ignores_a_placeholder_frame_count():
    one_second = b"\x00\x00" * 8000
    clip = _wav_with_placeholder_frame_count(one_second)
    with wave.open(io.BytesIO(clip), "rb") as audio:
        assert audio.getnframes() == 2147483647

    combined = concatenate_wavs([clip, clip])
    assert wav_duration_seconds(combined) == pytest.approx(2.0)


def test_audio_generation_expires_after_fifteen_minutes():
    now = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
    fresh = SimpleNamespace(
        audio_status=AUDIO_GENERATING,
        updated_at=now - timedelta(minutes=14),
    )
    stale = SimpleNamespace(
        audio_status=AUDIO_GENERATING,
        updated_at=now - timedelta(minutes=15),
    )
    ready = SimpleNamespace(audio_status=AUDIO_READY, updated_at=now)
    naive = SimpleNamespace(
        audio_status=AUDIO_GENERATING,
        updated_at=(now - timedelta(minutes=1)).replace(tzinfo=None),
    )

    assert audio_generation_in_progress(fresh, now=now)
    assert not audio_generation_in_progress(stale, now=now)
    assert not audio_generation_in_progress(ready, now=now)
    assert audio_generation_in_progress(naive, now=now)


def test_provider_message_keeps_the_terms_link():
    terms = (
        "The model requires terms acceptance. "
        "Please accept them at https://example.com/terms"
    )
    assert _provider_message(SimpleNamespace(body={"message": terms})) == terms
    nested = SimpleNamespace(body={"error": {"message": terms}})
    assert _provider_message(nested) == terms


def test_synthesize_speech_requires_a_key(monkeypatch):
    monkeypatch.delenv("SPEECH_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(AudioSynthesisError, match="GROQ_API_KEY"):
        synthesize_speech("Hello", "autumn")


def test_synthesize_speech_reads_wav_bytes(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    seen = {}

    class FakeResponse:
        def read(self):
            return b"RIFFwav"

    class FakeSpeech:
        def create(self, **kwargs):
            seen.update(kwargs)
            return FakeResponse()

    class FakeClient:
        def __init__(self, **kwargs):
            self.audio = SimpleNamespace(speech=FakeSpeech())

    monkeypatch.setattr("services.episode_audio.OpenAI", FakeClient)
    assert synthesize_speech("Hello", "austin") == b"RIFFwav"
    assert seen["voice"] == "austin"
    assert seen["response_format"] == "wav"
    assert seen["input"] == "Hello"


def test_local_storage_rejects_a_key_that_escapes_the_directory(tmp_path):
    storage = LocalEpisodeStorage(tmp_path)
    storage.put("episodes/1.wav", b"audio")
    assert b"".join(storage.stream("episodes/1.wav")) == b"audio"
    with pytest.raises(AudioStorageError):
        storage.put("../secret.wav", b"nope")
    storage.delete("episodes/1.wav")
    with pytest.raises(FileNotFoundError):
        b"".join(storage.stream("episodes/1.wav"))
