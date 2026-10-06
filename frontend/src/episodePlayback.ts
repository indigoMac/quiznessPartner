import type { EpisodeSegment, SegmentTiming } from "./types/api";

export interface EpisodeChapter {
  chapter: string;
  start: number;
  segmentIndex: number;
}

export function activeSegmentIndex(
  timings: SegmentTiming[],
  time: number
): number {
  if (!Number.isFinite(time)) return -1;
  for (let index = 0; index < timings.length; index += 1) {
    const timing = timings[index];
    const isLast = index === timings.length - 1;
    const contains = isLast
      ? time >= timing.start && time <= timing.end
      : time >= timing.start && time < timing.end;
    if (contains) return index;
  }
  return -1;
}

export function chapterStarts(
  script: EpisodeSegment[],
  timings: SegmentTiming[] | null | undefined
): EpisodeChapter[] {
  const chapters: EpisodeChapter[] = [];
  let previousChapter: string | null = null;
  script.forEach((segment, index) => {
    if (segment.chapter === previousChapter) return;
    previousChapter = segment.chapter;
    const start = timings?.[index]?.start;
    if (typeof start !== "number" || !Number.isFinite(start)) return;
    chapters.push({
      chapter: segment.chapter,
      start,
      segmentIndex: index,
    });
  });
  return chapters;
}

export function formatPlaybackTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const total = Math.floor(seconds);
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  return `${minutes}:${rest.toString().padStart(2, "0")}`;
}
