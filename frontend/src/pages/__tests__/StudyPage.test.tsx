import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import StudyPage from "../StudyPage";
import type { Episode, StudyTopicDetail } from "../../types/api";

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
  generate: {
    isPending: false,
    isError: false,
    error: null as Error | null,
    data: undefined as Episode | undefined,
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
}));

const topic: StudyTopicDetail = {
  id: 4,
  title: "Cell biology",
  topic: "Biology",
  source_url: null,
  can_practice: true,
};

function renderStudyPage() {
  return render(
    <MemoryRouter initialEntries={["/study/4"]}>
      <Routes>
        <Route path="/study/:id" element={<StudyPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("StudyPage", () => {
  beforeEach(() => {
    hooks.mutate.mockReset();
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
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
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

    await userEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(hooks.mutate).toHaveBeenCalledWith(4);
  });
});
