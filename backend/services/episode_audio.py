"""Turn a ready episode script into one audio file.

Speech runs after the HTTP response. Each host uses one voice. The provider
accepts at most 200 characters per request, so a segment is split, spoken in
order, and concatenated before its start and end are recorded.
"""

import io
import logging
import os
import wave
from datetime import datetime, timezone
from typing import List, Optional, Sequence
from uuid import uuid4

from openai import APIError, OpenAI
from sqlalchemy.orm import Session

from db import get_session_local
from models.episode import (
    AUDIO_FAILED,
    AUDIO_GENERATING,
    AUDIO_GENERATION_TIMEOUT,
    AUDIO_READY,
    EPISODE_READY,
    Episode,
)
from services.episode_storage import get_episode_storage

logger = logging.getLogger(__name__)

SPEECH_INPUT_CHAR_LIMIT = 200
AUDIO_JOB_STARTED = "started"
AUDIO_JOB_IN_PROGRESS = "in_progress"
AUDIO_JOB_ALREADY_READY = "already_ready"

_DEFAULT_SPEECH_BASE_URL = "https://api.groq.com/openai/v1"
_DEFAULT_SPEECH_MODEL = "canopylabs/orpheus-v1-english"
_DEFAULT_VOICES = {"host_a": "autumn", "host_b": "austin"}


class AudioSynthesisError(Exception):
    """Raised when episode audio cannot be synthesized or combined."""


def audio_generation_in_progress(episode, now: Optional[datetime] = None) -> bool:
    """True while a generating job is still inside the retry window."""
    if episode.audio_status != AUDIO_GENERATING:
        return False
    updated = episode.updated_at
    if updated is None:
        return False
    current = now or datetime.now(timezone.utc)
    elapsed = current - _as_utc(updated)
    return elapsed < AUDIO_GENERATION_TIMEOUT


def begin_episode_audio(db: Session, episode: Episode) -> str:
    """Claim the single audio job, or leave an active one alone.

    A ready file is left in place. Generating again is stage 6.
    """
    db.refresh(episode)
    if episode.audio_status == AUDIO_READY:
        return AUDIO_JOB_ALREADY_READY
    if audio_generation_in_progress(episode):
        return AUDIO_JOB_IN_PROGRESS

    episode.audio_status = AUDIO_GENERATING
    episode.audio_error = None
    episode.duration_seconds = None
    episode.segment_timings = None
    episode.audio_key = f"jobs/{uuid4().hex}"
    episode.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(episode)
    return AUDIO_JOB_STARTED


def timings_from_durations(durations: Sequence[float]) -> List[dict]:
    """Place each segment after the previous one, in seconds."""
    if not durations:
        raise AudioSynthesisError("Episode audio had no segments.")
    start = 0.0
    timings = []
    for duration in durations:
        if duration <= 0:
            raise AudioSynthesisError("A speech segment had no audio.")
        end = start + float(duration)
        timings.append({"start": start, "end": end})
        start = end
    return timings


def split_for_speech(text: str, limit: int = SPEECH_INPUT_CHAR_LIMIT) -> List[str]:
    """Split a line into provider-sized pieces without cutting a word."""
    cleaned = " ".join(text.split())
    if not cleaned:
        raise AudioSynthesisError("A script line was empty.")
    if len(cleaned) <= limit:
        return [cleaned]

    parts: List[str] = []
    remaining = cleaned
    while remaining:
        if len(remaining) <= limit:
            parts.append(remaining)
            break
        window = remaining[:limit]
        split_at = window.rfind(" ")
        if split_at <= 0:
            split_at = limit
        piece = remaining[:split_at].strip()
        if not piece:
            raise AudioSynthesisError("A script line could not be split for speech.")
        parts.append(piece)
        remaining = remaining[split_at:].strip()
    return parts


def wav_duration_seconds(data: bytes) -> float:
    with wave.open(io.BytesIO(data), "rb") as audio:
        rate = audio.getframerate()
        frames = audio.getnframes()
    if rate <= 0 or frames <= 0:
        raise AudioSynthesisError("Speech audio had no duration.")
    return frames / float(rate)


def concatenate_wavs(parts: Sequence[bytes]) -> bytes:
    """Join WAV pieces that share channels, width, and sample rate."""
    if not parts:
        raise AudioSynthesisError("No speech audio to combine.")
    frames: List[bytes] = []
    params = None
    for part in parts:
        try:
            with wave.open(io.BytesIO(part), "rb") as audio:
                if params is None:
                    params = audio.getparams()
                elif (
                    audio.getnchannels(),
                    audio.getsampwidth(),
                    audio.getframerate(),
                ) != (params.nchannels, params.sampwidth, params.framerate):
                    raise AudioSynthesisError(
                        "Speech segments did not use the same audio format."
                    )
                frames.append(audio.readframes(audio.getnframes()))
        except AudioSynthesisError:
            raise
        except wave.Error as exc:
            raise AudioSynthesisError("Speech audio was not a WAV file.") from exc
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setparams(params)
        for chunk in frames:
            audio.writeframes(chunk)
    return buffer.getvalue()


def episode_audio_key(episode_id: int) -> str:
    return f"episodes/{episode_id}.wav"


def voice_for_speaker(speaker: str) -> str:
    if speaker == "host_a":
        return os.getenv("SPEECH_VOICE_HOST_A", _DEFAULT_VOICES["host_a"])
    if speaker == "host_b":
        return os.getenv("SPEECH_VOICE_HOST_B", _DEFAULT_VOICES["host_b"])
    raise AudioSynthesisError("The episode script has an unknown speaker.")


def render_episode_audio(script: Sequence[dict]) -> tuple:
    """Return the combined WAV and one timing entry per script segment."""
    segment_wavs = []
    durations = []
    for segment in script:
        pieces = split_for_speech(segment.get("text") or "")
        voice = voice_for_speaker(segment.get("speaker") or "")
        piece_wavs = [synthesize_speech(piece, voice) for piece in pieces]
        segment_wav = concatenate_wavs(piece_wavs)
        segment_wavs.append(segment_wav)
        durations.append(wav_duration_seconds(segment_wav))
    timings = timings_from_durations(durations)
    return concatenate_wavs(segment_wavs), timings


def synthesize_speech(text: str, voice: str) -> bytes:
    """Request one WAV clip. text must already fit the provider limit."""
    if len(text) > SPEECH_INPUT_CHAR_LIMIT:
        raise AudioSynthesisError(
            "A speech request was longer than the provider allows."
        )
    api_key = _speech_api_key()
    if not api_key:
        raise AudioSynthesisError(
            "Speech is not configured. Set GROQ_API_KEY to generate audio."
        )
    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("SPEECH_BASE_URL", _speech_base_url()),
        timeout=60.0,
    )
    try:
        response = client.audio.speech.create(
            model=os.getenv("SPEECH_MODEL", _DEFAULT_SPEECH_MODEL),
            voice=voice,
            input=text,
            response_format="wav",
        )
        data = response.read()
    except APIError as exc:
        logger.warning("Speech request failed: %s", exc)
        detail = _provider_message(exc)
        raise AudioSynthesisError(
            f"Could not generate the episode audio. {detail}"
        ) from exc
    if not data:
        raise AudioSynthesisError("Speech came back empty.")
    return data


def synthesize_episode_audio(episode_id: int) -> None:
    """Run one claimed job. Leave the script untouched on failure."""
    claim, script, status = _load_audio_job(episode_id)
    if claim is None:
        return
    try:
        if status != EPISODE_READY or not script:
            raise AudioSynthesisError("The episode script is not ready for audio.")
        audio, timings = render_episode_audio(script)
    except AudioSynthesisError as exc:
        _finish_audio_job(episode_id, claim, error=str(exc))
        return
    except Exception:
        logger.exception("Episode %s audio failed", episode_id)
        _finish_audio_job(
            episode_id,
            claim,
            error="Could not generate the episode audio. Please try again.",
        )
        return

    key = episode_audio_key(episode_id)
    try:
        get_episode_storage().put(key, audio)
    except Exception:
        logger.exception("Episode %s audio could not be stored", episode_id)
        _finish_audio_job(
            episode_id,
            claim,
            error="Could not store the episode audio. Please try again.",
        )
        return
    _finish_audio_job(
        episode_id,
        claim,
        audio_key=key,
        duration_seconds=timings[-1]["end"],
        segment_timings=timings,
    )


def open_audio_session():
    return get_session_local()()


def _load_audio_job(episode_id: int):
    db = open_audio_session()
    try:
        episode = db.query(Episode).filter(Episode.id == episode_id).first()
        if episode is None or episode.audio_status != AUDIO_GENERATING:
            return None, None, None
        script = [dict(segment) for segment in (episode.script or [])]
        return episode.audio_key, script, episode.status
    finally:
        db.close()


def _finish_audio_job(
    episode_id: int,
    claim: str,
    *,
    error: Optional[str] = None,
    audio_key: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    segment_timings: Optional[list] = None,
) -> None:
    db = open_audio_session()
    try:
        episode = db.query(Episode).filter(Episode.id == episode_id).first()
        if (
            episode is None
            or episode.audio_status != AUDIO_GENERATING
            or episode.audio_key != claim
        ):
            return
        if error is None:
            episode.audio_status = AUDIO_READY
            episode.audio_error = None
            episode.audio_key = audio_key
            episode.duration_seconds = duration_seconds
            episode.segment_timings = segment_timings
        else:
            episode.audio_status = AUDIO_FAILED
            episode.audio_error = error
            episode.duration_seconds = None
            episode.segment_timings = None
            episode.audio_key = None
        episode.updated_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()


def _provider_message(exc: BaseException) -> str:
    """Use the provider's own sentence, including any terms link."""
    body = getattr(exc, "body", None)
    text = str(exc)
    if isinstance(body, dict):
        nested = body.get("error")
        if isinstance(nested, dict) and nested.get("message"):
            text = str(nested["message"])
        elif body.get("message"):
            text = str(body["message"])
    cleaned = " ".join(text.split())
    return cleaned[:500]


def _speech_api_key() -> str:
    return (
        os.getenv("SPEECH_API_KEY")
        or os.getenv("GROQ_API_KEY")
        or os.getenv("LLM_API_KEY")
        or ""
    )


def _speech_base_url() -> str:
    return os.getenv("LLM_BASE_URL", _DEFAULT_SPEECH_BASE_URL)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
