import { useEffect, useRef, useState } from "react";
import { getEpisodeAudio } from "../api/quizApi";
import {
  formatPlaybackTime,
  type EpisodeChapter,
} from "../episodePlayback";
import Button from "./Button";

interface EpisodePlayerProps {
  studyTopicId: number;
  durationSeconds: number | null;
  chapters: EpisodeChapter[];
  onTimeUpdate: (time: number) => void;
}

function clampTime(audio: HTMLAudioElement, seconds: number) {
  const next = Math.max(0, seconds);
  if (Number.isFinite(audio.duration) && audio.duration > 0) {
    return Math.min(next, audio.duration);
  }
  return next;
}

export default function EpisodePlayer({
  studyTopicId,
  durationSeconds,
  chapters,
  onTimeUpdate,
}: EpisodePlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const pendingSeek = useRef<number | null>(null);
  const onTimeUpdateRef = useRef(onTimeUpdate);
  const publishedTime = useRef(0);
  onTimeUpdateRef.current = onTimeUpdate;
  const [src, setSrc] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [mediaDuration, setMediaDuration] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const duration =
    mediaDuration != null && mediaDuration > 0
      ? mediaDuration
      : durationSeconds != null && durationSeconds > 0
        ? durationSeconds
        : 0;
  const canControl = Boolean(src) && !loadError;

  useEffect(() => {
    let cancelled = false;
    let objectUrl: string | null = null;
    setSrc(null);
    setLoadError(null);
    setPlaying(false);
    setMediaDuration(null);
    publishedTime.current = 0;
    setCurrentTime(0);
    onTimeUpdateRef.current(0);

    getEpisodeAudio(studyTopicId)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setLoadError(
          error instanceof Error && error.message
            ? error.message
            : "Could not load the episode audio."
        );
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [studyTopicId]);

  function publish(time: number) {
    if (publishedTime.current === time) return;
    publishedTime.current = time;
    setCurrentTime(time);
    onTimeUpdateRef.current(time);
  }

  function seek(seconds: number) {
    const audio = audioRef.current;
    if (!audio || !src) {
      pendingSeek.current = Math.max(0, seconds);
      publish(pendingSeek.current);
      return;
    }
    const next = clampTime(audio, seconds);
    audio.currentTime = next;
    pendingSeek.current = null;
    publish(next);
  }

  async function togglePlayback() {
    const audio = audioRef.current;
    if (!audio || !canControl) return;
    if (!playing) {
      try {
        await audio.play();
      } catch (error) {
        setLoadError(
          error instanceof Error && error.message
            ? error.message
            : "Could not play the episode audio."
        );
      }
      return;
    }
    audio.pause();
  }

  function handleLoadedMetadata() {
    const audio = audioRef.current;
    if (!audio) return;
    if (Number.isFinite(audio.duration) && audio.duration > 0) {
      setMediaDuration(audio.duration);
    }
    if (pendingSeek.current == null) return;
    const next = clampTime(audio, pendingSeek.current);
    audio.currentTime = next;
    pendingSeek.current = null;
    publish(next);
  }

  return (
    <div className="mt-4 min-w-0 max-w-full space-y-3" data-testid="episode-player">
      {loadError ? (
        <p className="break-words text-red-700 dark:text-red-400" role="alert">
          {loadError}
        </p>
      ) : (
        <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-center">
          <Button
            type="button"
            className="w-full shrink-0 sm:w-auto"
            onClick={togglePlayback}
            disabled={!canControl}
          >
            {playing ? "Pause" : "Play"}
          </Button>
          <div className="min-w-0 flex-1">
            <input
              type="range"
              aria-label="Seek"
              min={0}
              max={duration || 0}
              step={0.1}
              value={Math.min(currentTime, duration || 0)}
              disabled={!canControl}
              onChange={(event) => seek(Number(event.target.value))}
              className="block h-2 w-full min-w-0 accent-teal-800"
            />
            <div className="mt-1 flex justify-between gap-3 text-xs tabular-nums text-stone-500 dark:text-stone-400">
              <span>{formatPlaybackTime(currentTime)}</span>
              <span>{formatPlaybackTime(duration)}</span>
            </div>
          </div>
        </div>
      )}
      {chapters.length > 0 && (
        <nav
          aria-label="Chapters"
          className="flex min-w-0 flex-col gap-2 sm:flex-row sm:flex-wrap"
        >
          {chapters.map((chapter) => (
            <button
              key={`${chapter.segmentIndex}-${chapter.chapter}`}
              type="button"
              disabled={!canControl}
              onClick={() => seek(chapter.start)}
              className="min-h-11 w-full min-w-0 max-w-full break-words rounded-xl border border-stone-300 bg-white px-3 py-2 text-left text-sm font-semibold text-stone-800 hover:bg-stone-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-stone-600 dark:bg-transparent dark:text-stone-200 dark:hover:bg-stone-800 sm:w-auto"
            >
              {chapter.chapter}
            </button>
          ))}
        </nav>
      )}
      <audio
        ref={audioRef}
        data-testid="episode-audio"
        className="block h-0 w-0 overflow-hidden"
        preload="auto"
        src={src ?? undefined}
        onTimeUpdate={() => publish(audioRef.current?.currentTime ?? 0)}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
      />
    </div>
  );
}
