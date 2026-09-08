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
      quizzes: [
        {
          id: 42,
          title: "Quiz on Geography",
          topic: "Geography",
          created_at: "2026-01-15T00:00:00",
          question_count: 5,
          attempt_count: 2,
          best_score: 4,
          study_topic_id: 7,
        },
      ],
      study_topics: [
        {
          id: 7,
          title: "Geography",
          topic: "Geography",
          can_practice: true,
          quiz_count: 1,
          completed: 1,
          quizzes: [
            {
              id: 42,
              title: "Quiz on Geography",
              topic: "Geography",
              created_at: "2026-01-15T00:00:00",
              question_count: 5,
              attempt_count: 2,
              best_score: 4,
              study_topic_id: 7,
            },
          ],
        },
      ],
      total_quizzes: 1,
      completed: 1,
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

describe("Dashboard with quizzes", () => {
  it("renders saved quizzes and stats", () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    expect(screen.getByText("Quiz on Geography")).toBeInTheDocument();
    expect(screen.getByText(/Best score: 4/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /quiz on geography/i })).toHaveAttribute(
      "href",
      "/quiz/42"
    );
    expect(screen.getByRole("button", { name: /new quiz on this topic/i })).toBeInTheDocument();
    expect(screen.getByText("Total Quizzes")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
  });
});
