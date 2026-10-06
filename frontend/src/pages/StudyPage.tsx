import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Button from "../components/Button";
import EpisodePlayer from "../components/EpisodePlayer";
import { activeSegmentIndex, chapterStarts } from "../episodePlayback";
import {
  useGenerateStudyAudio,
  useGenerateStudyEpisode,
  useStudyEpisode,
  useStudyTopic,
} from "../hooks/useQuiz";
import type { Episode, EpisodeSegment } from "../types/api";

function topicIdFromParam(id: string | undefined): number | null {
  const parsed = Number(id);
  if (!Number.isInteger(parsed) || parsed <= 0) return null;
  return parsed;
}

function groupByChapter(script: EpisodeSegment[]) {
  const chapters: {
    chapter: string;
    lines: { segment: EpisodeSegment; index: number }[];
  }[] = [];
  script.forEach((segment, index) => {
    const current = chapters[chapters.length - 1];
    const line = { segment, index };
    if (current && current.chapter === segment.chapter) {
      current.lines.push(line);
    } else {
      chapters.push({ chapter: segment.chapter, lines: [line] });
    }
  });
  return chapters;
}

function hostLabel(speaker: EpisodeSegment["speaker"]) {
  return speaker === "host_a" ? "Host A" : "Host B";
}

function hostLineClass(speaker: EpisodeSegment["speaker"], active: boolean) {
  const tone =
    speaker === "host_a"
      ? "border-teal-200 bg-teal-50 dark:border-teal-900 dark:bg-teal-950/40"
      : "border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/40";
  const current = active ? "ring-2 ring-inset ring-teal-800 dark:ring-teal-300" : "";
  return `min-w-0 max-w-full break-words rounded-xl border px-4 py-3 ${tone} ${current}`;
}

function HostLine({
  line,
  active,
}: {
  line: EpisodeSegment;
  active: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!active) return;
    ref.current?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }, [active]);

  return (
    <div
      ref={ref}
      data-testid="host-line"
      data-speaker={line.speaker}
      data-active={active ? "true" : "false"}
      aria-current={active ? "true" : undefined}
      className={hostLineClass(line.speaker, active)}
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-stone-500 dark:text-stone-400">
        {hostLabel(line.speaker)}
      </p>
      <p className="mt-1 break-words text-stone-800 dark:text-stone-100">
        {line.text}
      </p>
    </div>
  );
}

function audioFailureMessage(episode: Episode | undefined, audioError: unknown) {
  if (audioError instanceof Error && audioError.message) {
    return audioError.message;
  }
  if (episode?.audio_status === "failed") {
    return (
      episode.audio_error ||
      "Could not generate the episode audio. Please try again."
    );
  }
  return "Could not generate the episode audio. Please try again.";
}

function failureMessage(
  episode: Episode | undefined,
  generateError: unknown,
  episodeError: unknown
) {
  if (generateError instanceof Error && generateError.message) {
    return generateError.message;
  }
  if (episode?.status === "failed") {
    return (
      episode.error_message ||
      "The episode could not be written. Please try again."
    );
  }
  if (episodeError instanceof Error && episodeError.message) {
    return episodeError.message;
  }
  return "The episode could not be written. Please try again.";
}

export default function StudyPage() {
  const { id } = useParams<{ id: string }>();
  const topicId = topicIdFromParam(id);
  const topicQuery = useStudyTopic(topicId);
  const episodeQuery = useStudyEpisode(topicQuery.isSuccess ? topicId : null);
  const generate = useGenerateStudyEpisode();
  const generateAudio = useGenerateStudyAudio();

  const topic = topicQuery.data;
  const episode = episodeQuery.data ?? generate.data ?? generateAudio.data;
  const script =
    episode?.status === "ready" && episode.script ? episode.script : null;
  const writing =
    topicQuery.isLoading ||
    generate.isPending ||
    (episodeQuery.isLoading && !script);
  const failed =
    !writing &&
    (generate.isError ||
      episodeQuery.isError ||
      episode?.status === "failed");

  const retry = () => {
    if (topicId) generate.mutate(topicId);
  };
  const startAudio = () => {
    if (topicId) generateAudio.mutate(topicId);
  };
  const [currentTime, setCurrentTime] = useState(0);
  const audioStatus = episode?.audio_status ?? "none";
  const audioGenerating = audioStatus === "generating" || generateAudio.isPending;
  const audioFailed =
    !audioGenerating && (audioStatus === "failed" || generateAudio.isError);
  const audioReady = Boolean(script) && audioStatus === "ready" && !audioGenerating;
  const activeIndex =
    audioReady && episode?.segment_timings
      ? activeSegmentIndex(episode.segment_timings, currentTime)
      : -1;

  useEffect(() => {
    setCurrentTime(0);
  }, [topicId]);

  if (!topicId || (topicQuery.isError && !topic)) {
    const message =
      topicQuery.error instanceof Error
        ? topicQuery.error.message
        : "Study topic not found.";
    return (
      <div className="card p-5 sm:p-6 text-center">
        <h2 className="font-display text-2xl font-semibold mb-3">
          Study topic not found
        </h2>
        <p className="text-stone-600 dark:text-stone-400 mb-6">{message}</p>
        <Link to="/dashboard" className="inline-block">
          <Button>Back to dashboard</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="min-w-0 space-y-6">
      <div className="card p-5 sm:p-6">
        <p className="page-kicker mb-2">Episode</p>
        <h2 className="page-title text-2xl sm:text-3xl mb-2">
          {topic?.title || "Study topic"}
        </h2>
        {script && episode?.title && (
          <p className="text-lg text-stone-700 dark:text-stone-200">
            {episode.title}
          </p>
        )}
        {topic?.source_url && (
          <p className="mt-2 text-sm text-stone-500 dark:text-stone-400 break-all">
            {topic.source_url}
          </p>
        )}
        {script && audioGenerating && (
          <div className="mt-4 flex items-center gap-3" data-testid="audio-progress">
            <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-teal-700" />
            <p className="text-stone-600 dark:text-stone-300">Generating audio...</p>
          </div>
        )}
        {script && audioFailed && (
          <div className="mt-4" role="alert">
            <p className="text-red-700 dark:text-red-400 break-words">
              {audioFailureMessage(episode, generateAudio.error)}
            </p>
            <Button
              className="mt-4"
              onClick={startAudio}
              isLoading={generateAudio.isPending}
            >
              Generate audio
            </Button>
          </div>
        )}
        {script && !audioGenerating && !audioFailed && audioStatus === "none" && (
          <Button className="mt-4" onClick={startAudio}>
            Generate audio
          </Button>
        )}
        {audioReady && topicId && script && (
          <EpisodePlayer
            studyTopicId={topicId}
            durationSeconds={episode?.duration_seconds ?? null}
            chapters={chapterStarts(script, episode?.segment_timings)}
            onTimeUpdate={setCurrentTime}
          />
        )}
      </div>

      {writing && (
        <div className="card p-5 sm:p-6 flex items-center gap-3">
          <div
            data-testid="loading-spinner"
            className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-teal-700"
          />
          <p className="text-stone-600 dark:text-stone-300">
            Writing the episode...
          </p>
        </div>
      )}

      {failed && (
        <div className="card p-5 sm:p-6" role="alert">
          <p className="text-red-700 dark:text-red-400">
            {failureMessage(episode, generate.error, episodeQuery.error)}
          </p>
          <Button className="mt-4" onClick={retry} isLoading={generate.isPending}>
            Try again
          </Button>
        </div>
      )}

      {script &&
        groupByChapter(script).map((chapter, chapterIndex) => (
          <section
            key={`${chapter.chapter}-${chapterIndex}`}
            className="card min-w-0 space-y-4 p-5 sm:p-6"
          >
            <h3 className="font-display text-xl font-semibold">
              {chapter.chapter}
            </h3>
            <div className="space-y-3">
              {chapter.lines.map((line) => (
                <HostLine
                  key={`${line.index}-${line.segment.speaker}`}
                  line={line.segment}
                  active={line.index === activeIndex}
                />
              ))}
            </div>
          </section>
        ))}
    </div>
  );
}
