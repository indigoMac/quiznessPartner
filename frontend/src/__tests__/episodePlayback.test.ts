import { describe, expect, it } from "vitest";
import {
  activeSegmentIndex,
  chapterStarts,
  formatPlaybackTime,
} from "../episodePlayback";
import type { EpisodeSegment, SegmentTiming } from "../types/api";

const timings: SegmentTiming[] = [
  { start: 0, end: 8 },
  { start: 8, end: 12 },
  { start: 12, end: 20 },
];

const script: EpisodeSegment[] = [
  { chapter: "Chapter One", speaker: "host_a", text: "Opening line" },
  { chapter: "Chapter One", speaker: "host_b", text: "Reply line" },
  { chapter: "Chapter Two", speaker: "host_a", text: "Next line" },
];

describe("activeSegmentIndex", () => {
  it("moves to the next segment when time crosses a boundary", () => {
    expect(activeSegmentIndex(timings, 7.9)).toBe(0);
    expect(activeSegmentIndex(timings, 8)).toBe(1);
    expect(activeSegmentIndex(timings, 12)).toBe(2);
    expect(activeSegmentIndex(timings, 20)).toBe(2);
    expect(activeSegmentIndex(timings, 20.1)).toBe(-1);
  });
});

describe("chapterStarts", () => {
  it("uses the first segment of each chapter", () => {
    expect(chapterStarts(script, timings)).toEqual([
      { chapter: "Chapter One", start: 0, segmentIndex: 0 },
      { chapter: "Chapter Two", start: 12, segmentIndex: 2 },
    ]);
  });
});

describe("formatPlaybackTime", () => {
  it("renders minutes and seconds", () => {
    expect(formatPlaybackTime(0)).toBe("0:00");
    expect(formatPlaybackTime(65)).toBe("1:05");
    expect(formatPlaybackTime(Number.NaN)).toBe("0:00");
  });
});
