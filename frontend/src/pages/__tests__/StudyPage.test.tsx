import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import StudyPage from "../StudyPage";
import type { Episode, QuizSummary, StudyTopicDetail } from "../../types/api";
import { INSUFFICIENT_STUDY_MATERIAL } from "../../types/api";

const audioApi = vi.hoisted(() => ({
  getEpisodeAudio: vi.fn(),
}));

vi.mock("../../api/quizApi", () => ({
  getEpisodeAudio: (...args: unknown[]) => audioApi.getEpisodeAudio(...args),
}));

const hooks = vi.hoisted(() => ({
  topic: {
    data: undefined as StudyTopicDetail | undefined,
    isLoading: false,
    isSuccess: true,
    isError: false,
    error: null as Error | null,
  },
  episode: {
    data: undefined as Episode | undefined,
    isLoading: false,
    isError: false,
    error: null as Error | null,
  },
  mutate: vi.fn(),
  generateAudio: vi.fn(),
  generate: {
    isPending: false,
    isError: false,
    error: null as Error | null,
    data: undefined as Episode | undefined,
  },
  audio: {
    isPending: false,
    isError: false,
    error: null as Error | null,
  },
  practice: {
    mutateAsync: vi.fn(),
    isPending: false,
    isError: false,
    error: null as Error | null,
  },
}));

vi.mock("../../hooks/useQuiz", () => ({
  useStudyTopic: () => hooks.topic,
  useStudyEpisode: () => hooks.episode,
  useGenerateStudyEpisode: () => ({
    mutate: hooks.mutate,
    isPending: hooks.generate.isPending,
    isError: hooks.generate.isError,
    error: hooks.generate.error,
    data: hooks.generate.data,
  }),
  useGenerateStudyAudio: () => ({
    mutate: hooks.generateAudio,
    isPending: hooks.audio.isPending,
    isError: hooks.audio.isError,
    error: hooks.audio.error,
  }),
  usePracticeStudyTopic: () => hooks.practice,
}));

const topic: StudyTopicDetail = {
  id: 4,
  title: "Cell biology",
  topic: "Biology",
  source_url: null,
  can_practice: true,
  has_source: true,
  quizzes: [],
};

function renderStudyPage() {
  return render(
    <MemoryRouter initialEntries={["/study/4"]}>
      <Routes>
        <Route path="/study/:id" element={<StudyPage />} />
        <Route path="/quiz/:id" element={<p>Opened quiz</p>} />
      </Routes>
    </MemoryRouter>
  );
}

const readyEpisode: Episode = {
  id: 9,
  study_topic_id: 4,
  status: "ready",
  title: "How cells divide",
  script: [
    { chapter: "Chapter One", speaker: "host_a", text: "Opening line" },
    { chapter: "Chapter One", speaker: "host_b", text: "Reply line" },
    { chapter: "Chapter Two", speaker: "host_a", text: "Next line" },
  ],
  audio_status: "ready",
  duration_seconds: 20,
  segment_timings: [
    { start: 0, end: 8 },
    { start: 8, end: 12 },
    { start: 12, end: 20 },
  ],
};

async function playerControls() {
  const play = await screen.findByRole("button", { name: "Play" });
  expect(play).toBeEnabled();
  return screen.getByTestId("episode-audio") as HTMLAudioElement;
}

describe("StudyPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    hooks.mutate.mockReset();
    hooks.generateAudio.mockReset();
    audioApi.getEpisodeAudio.mockReset();
    audioApi.getEpisodeAudio.mockResolvedValue(
      new Blob(["RIFF"], { type: "audio/wav" })
    );
    if (typeof URL.createObjectURL !== "function") {
      Object.defineProperty(URL, "createObjectURL", {
        configurable: true,
        value: vi.fn(() => "blob:episode-audio"),
      });
    } else {
      vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:episode-audio");
    }
    if (typeof URL.revokeObjectURL !== "function") {
      Object.defineProperty(URL, "revokeObjectURL", {
        configurable: true,
        value: vi.fn(),
      });
    }
    hooks.topic = {
      data: topic,
      isLoading: false,
      isSuccess: true,
      isError: false,
      error: null,
    };
    hooks.episode = {
      data: undefined,
      isLoading: false,
      isError: false,
      error: null,
    };
    hooks.generate = {
      isPending: false,
      isError: false,
      error: null,
      data: undefined,
    };
    hooks.audio = {
      isPending: false,
      isError: false,
      error: null,
    };
    hooks.practice.mutateAsync.mockReset();
    hooks.practice.mutateAsync.mockResolvedValue({ id: "15" });
    hooks.practice.isPending = false;
    hooks.practice.isError = false;
    hooks.practice.error = null;
  });

  it("renders host lines in chapter order", () => {
    hooks.episode.data = {
      id: 9,
      study_topic_id: 4,
      status: "ready",
      title: "How cells divide",
      error_message: null,
      script: [
        {
          chapter: "Chapter One",
          speaker: "host_a",
          text: "Opening line",
        },
        {
          chapter: "Chapter One",
          speaker: "host_b",
          text: "Reply line",
        },
        {
          chapter: "Chapter Two",
          speaker: "host_a",
          text: "Next line",
        },
      ],
    };

    renderStudyPage();

    expect(screen.getByRole("heading", { name: "Cell biology" })).toBeInTheDocument();
    expect(screen.getByText("How cells divide")).toBeInTheDocument();
    const chapters = screen.getAllByRole("heading", { level: 3 });
    expect(chapters.map((heading) => heading.textContent)).toEqual([
      "Quizzes",
      "Chapter One",
      "Chapter Two",
    ]);

    const lines = screen.getAllByTestId("host-line");
    expect(lines).toHaveLength(3);
    expect(lines[0]).toHaveTextContent("Host A");
    expect(lines[0]).toHaveTextContent("Opening line");
    expect(lines[0]).toHaveAttribute("data-speaker", "host_a");
    expect(lines[1]).toHaveTextContent("Host B");
    expect(lines[1]).toHaveTextContent("Reply line");
    expect(lines[1]).toHaveAttribute("data-speaker", "host_b");
    expect(lines[2]).toHaveTextContent("Host A");
    expect(lines[2]).toHaveTextContent("Next line");
    expect(lines[0].className).not.toEqual(lines[1].className);
    expect(lines.every((line) => line.getAttribute("data-active") === "false")).toBe(
      true
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByTestId("episode-player")).not.toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Chapters" })).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Generate audio" })
    ).toBeInTheDocument();
  });

  it("starts audio generation and shows progress", async () => {
    hooks.episode.data = {
      id: 9,
      study_topic_id: 4,
      status: "ready",
      title: "How cells divide",
      script: [
        { chapter: "Chapter One", speaker: "host_a", text: "Opening line" },
      ],
      audio_status: "generating",
    };

    renderStudyPage();

    expect(screen.getByTestId("audio-progress")).toHaveTextContent(
      "Generating audio..."
    );
    expect(
      screen.queryByRole("button", { name: "Generate audio" })
    ).not.toBeInTheDocument();
    expect(screen.getByText("Opening line")).toBeInTheDocument();
  });

  it("starts audio from a ready script", async () => {
    hooks.episode.data = {
      id: 9,
      study_topic_id: 4,
      status: "ready",
      title: "How cells divide",
      script: [
        { chapter: "Chapter One", speaker: "host_a", text: "Opening line" },
      ],
      audio_status: "none",
    };

    renderStudyPage();
    await userEvent.click(screen.getByRole("button", { name: "Generate audio" }));
    expect(hooks.generateAudio).toHaveBeenCalledWith(4);
  });

  it("shows an audio failure without hiding the script", () => {
    hooks.episode.data = {
      id: 9,
      study_topic_id: 4,
      status: "ready",
      title: "How cells divide",
      script: [
        { chapter: "Chapter One", speaker: "host_a", text: "Opening line" },
      ],
      audio_status: "failed",
      audio_error: "Speech provider rejected the line.",
    };

    renderStudyPage();

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Speech provider rejected the line."
    );
    expect(screen.getByText("Opening line")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generate audio" })).toBeInTheDocument();
  });

  it("shows the error and retries a failed episode", async () => {
    hooks.episode.data = {
      id: 9,
      study_topic_id: 4,
      status: "failed",
      title: null,
      script: null,
      error_message: "Episode script was not valid JSON.",
    };

    renderStudyPage();

    expect(screen.getByRole("heading", { name: "Cell biology" })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Episode script was not valid JSON."
    );
    expect(screen.queryByTestId("host-line")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Generate audio" })
    ).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(hooks.mutate).toHaveBeenCalledWith(4);
  });

  it("highlights the segment for the current time", async () => {
    hooks.episode.data = readyEpisode;
    const scroll = vi.mocked(window.HTMLElement.prototype.scrollIntoView);

    renderStudyPage();
    const audio = await playerControls();
    const lines = screen.getAllByTestId("host-line");
    expect(lines[0]).toHaveAttribute("data-active", "true");
    expect(lines[1]).toHaveAttribute("data-active", "false");
    scroll.mockClear();

    audio.currentTime = 8;
    fireEvent.timeUpdate(audio);

    expect(lines[1]).toHaveAttribute("data-active", "true");
    expect(lines[0]).toHaveAttribute("data-active", "false");
    expect(lines[1]).toHaveAttribute("aria-current", "true");
    expect(scroll).toHaveBeenCalled();
  });

  it("seeks to a chapter start", async () => {
    hooks.episode.data = readyEpisode;
    renderStudyPage();
    const audio = await playerControls();

    fireEvent.click(screen.getByRole("button", { name: "Chapter Two" }));

    expect(audio.currentTime).toBe(12);
    const lines = screen.getAllByTestId("host-line");
    expect(lines[2]).toHaveAttribute("data-active", "true");
    expect(lines[0]).toHaveAttribute("data-active", "false");
  });

  it("plays, pauses, and seeks from the slider", async () => {
    hooks.episode.data = readyEpisode;
    const play = vi
      .spyOn(HTMLMediaElement.prototype, "play")
      .mockImplementation(function mockPlay(this: HTMLMediaElement) {
        this.dispatchEvent(new Event("play"));
        return Promise.resolve();
      });
    const pause = vi
      .spyOn(HTMLMediaElement.prototype, "pause")
      .mockImplementation(function mockPause(this: HTMLMediaElement) {
        this.dispatchEvent(new Event("pause"));
      });

    renderStudyPage();
    const audio = await playerControls();
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    expect(play).toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Pause" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    expect(pause).toHaveBeenCalled();

    fireEvent.change(screen.getByRole("slider", { name: "Seek" }), {
      target: { value: "5" },
    });
    expect(audio.currentTime).toBe(5);
    expect(screen.getAllByTestId("host-line")[0]).toHaveAttribute("data-active", "true");
  });

  it("shows an audio load error and keeps the script", async () => {
    hooks.episode.data = readyEpisode;
    audioApi.getEpisodeAudio.mockRejectedValue(
      new Error("Episode audio was not found.")
    );

    renderStudyPage();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Episode audio was not found."
    );
    expect(screen.getByText("Opening line")).toBeInTheDocument();
    expect(screen.getByText("Next line")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Play" })).not.toBeInTheDocument();
  });

  it("generates a test from the topic and opens the quiz", async () => {
    const savedQuiz: QuizSummary = {
      id: 42,
      title: "Mitosis check",
      topic: "Biology",
      created_at: "2026-01-15T00:00:00",
      question_count: 5,
      attempt_count: 1,
      best_score: 4,
      study_topic_id: 4,
      difficulty: "medium",
    };
    hooks.topic.data = { ...topic, quizzes: [savedQuiz] };
    hooks.episode.data = {
      id: 9,
      study_topic_id: 4,
      status: "ready",
      title: "How cells divide",
      script: [
        { chapter: "Chapter One", speaker: "host_a", text: "Opening line" },
      ],
      audio_status: "none",
    };

    renderStudyPage();

    const quizLink = screen.getByRole("link", { name: /mitosis check/i });
    expect(quizLink).toHaveAttribute("href", "/quiz/42");
    expect(quizLink).toHaveTextContent("5 questions");
    expect(quizLink).toHaveTextContent("Medium");
    expect(quizLink).toHaveTextContent("Best score: 4");
    expect(screen.getByRole("button", { name: "Generate audio" })).toBeEnabled();

    fireEvent.change(screen.getByLabelText("Number of Questions"), {
      target: { value: "3" },
    });
    fireEvent.change(screen.getByLabelText("Difficulty"), {
      target: { value: "hard" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Generate a test" }));

    expect(hooks.practice.mutateAsync).toHaveBeenCalledWith({
      study_topic_id: 4,
      num_questions: 3,
      difficulty: "hard",
    });
    expect(await screen.findByText("Opened quiz")).toBeInTheDocument();
  });

  it("keeps generate a test disabled when the topic has no source", () => {
    hooks.topic.data = { ...topic, has_source: false, can_practice: false };
    hooks.practice.isError = true;
    hooks.practice.error = new Error(INSUFFICIENT_STUDY_MATERIAL);

    renderStudyPage();

    expect(screen.getByRole("button", { name: "Generate a test" })).toBeDisabled();
    expect(screen.getByRole("alert")).toHaveTextContent(INSUFFICIENT_STUDY_MATERIAL);
    expect(hooks.practice.mutateAsync).not.toHaveBeenCalled();
  });
});
