import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Dashboard from "../Dashboard";

vi.mock("../../context/AuthContext", () => ({
  useAuth: () => ({
    user: { id: 1, email: "test@example.com" },
  }),
}));

vi.mock("../../hooks/useQuiz", () => ({
  useMyQuizzes: () => ({
    data: {
      quizzes: [],
      study_topics: [
        {
          id: 4,
          title: "notes.txt",
          topic: null,
          source_label: "Saved text",
          can_practice: true,
          quiz_count: 0,
          completed: 0,
          quizzes: [],
        },
      ],
      total_quizzes: 0,
      completed: 0,
      total_topics: 1,
    },
    isLoading: false,
    error: null,
  }),
  usePracticeStudyTopic: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
    isError: false,
    variables: undefined,
  }),
}));

describe("Dashboard with saved material", () => {
  it("shows a topic that has no quizzes yet", () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    expect(screen.getByText("notes.txt")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "notes.txt" })).toHaveAttribute(
      "href",
      "/study/4"
    );
    expect(screen.getByText("Saved text")).toBeInTheDocument();
    expect(screen.getByText("No quizzes yet.")).toBeInTheDocument();
    expect(screen.queryByText("No quizzes created yet.")).not.toBeInTheDocument();
  });
});
