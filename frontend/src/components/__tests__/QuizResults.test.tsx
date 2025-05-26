import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import QuizResults from "../QuizResults";
import type { QuizResult } from "../../types/api";

// Mock Material-UI components
vi.mock("@mui/material", () => ({
  Box: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  Typography: ({ children, ...props }: any) => <p {...props}>{children}</p>,
  Button: ({ children, onClick, ...props }: any) => (
    <button onClick={onClick} {...props}>
      {children}
    </button>
  ),
  CircularProgress: ({ value, ...props }: any) => (
    <div role="progressbar" aria-valuenow={value} {...props} />
  ),
}));

describe("QuizResults", () => {
  const mockResult = {
    score: 7,
    total: 10,
  };

  const mockOnNewQuiz = vi.fn();
  const mockOnRetry = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("displays the score percentage correctly", () => {
    render(
      <QuizResults
        result={mockResult}
        onNewQuiz={mockOnNewQuiz}
        onRetry={mockOnRetry}
      />
    );

    expect(screen.getByText("70%")).toBeInTheDocument();
  });

  it("displays the appropriate score message", () => {
    render(
      <QuizResults
        result={mockResult}
        onNewQuiz={mockOnNewQuiz}
        onRetry={mockOnRetry}
      />
    );

    expect(screen.getByText("Great job!")).toBeInTheDocument();
  });

  it("displays the score details", () => {
    render(
      <QuizResults
        result={mockResult}
        onNewQuiz={mockOnNewQuiz}
        onRetry={mockOnRetry}
      />
    );

    expect(
      screen.getByText("You scored 7 out of 10 questions correctly.")
    ).toBeInTheDocument();
  });

  it("calls onRetry when Try Again button is clicked", async () => {
    const user = userEvent.setup();
    render(
      <QuizResults
        result={mockResult}
        onNewQuiz={mockOnNewQuiz}
        onRetry={mockOnRetry}
      />
    );

    await user.click(screen.getByText("Try Again"));
    expect(mockOnRetry).toHaveBeenCalled();
  });

  it("calls onNewQuiz when Create New Quiz button is clicked", async () => {
    const user = userEvent.setup();
    render(
      <QuizResults
        result={mockResult}
        onNewQuiz={mockOnNewQuiz}
        onRetry={mockOnRetry}
      />
    );

    await user.click(screen.getByText("Create New Quiz"));
    expect(mockOnNewQuiz).toHaveBeenCalled();
  });
});
