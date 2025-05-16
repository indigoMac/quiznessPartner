import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import QuizResults from "../QuizResults";
import type { QuizResult } from "../../types/api";

describe("QuizResults Component", () => {
  const createMockResult = (score: number, total: number): QuizResult => ({
    quiz_id: 1,
    score,
    total,
    answers: [0, 1, 2],
    correct_answers: [0, 2, 2],
  });

  const defaultProps = {
    result: createMockResult(3, 5),
    onRetry: vi.fn(),
    onNewQuiz: vi.fn(),
  };

  it("renders the score percentage correctly", () => {
    render(<QuizResults {...defaultProps} />);
    expect(screen.getByText("60%")).toBeInTheDocument();
  });

  it("displays the correct score text", () => {
    render(<QuizResults {...defaultProps} />);
    expect(
      screen.getByText("You scored 3 out of 5 questions correctly.")
    ).toBeInTheDocument();
  });

  it("shows 'Excellent!' message for scores >= 90%", () => {
    const highResult = createMockResult(9, 10); // 90%
    render(<QuizResults {...defaultProps} result={highResult} />);
    expect(screen.getByText("Excellent!")).toBeInTheDocument();
  });

  it("shows 'Great job!' message for scores >= 70% and < 90%", () => {
    const goodResult = createMockResult(7, 10); // 70%
    render(<QuizResults {...defaultProps} result={goodResult} />);
    expect(screen.getByText("Great job!")).toBeInTheDocument();
  });

  it("shows 'Good effort!' message for scores >= 50% and < 70%", () => {
    const averageResult = createMockResult(5, 10); // 50%
    render(<QuizResults {...defaultProps} result={averageResult} />);
    expect(screen.getByText("Good effort!")).toBeInTheDocument();
  });

  it("shows 'Keep learning!' message for scores < 50%", () => {
    const lowResult = createMockResult(4, 10); // 40%
    render(<QuizResults {...defaultProps} result={lowResult} />);
    expect(screen.getByText("Keep learning!")).toBeInTheDocument();
  });

  it("applies green text color for scores >= 90%", () => {
    const highResult = createMockResult(9, 10); // 90%
    render(<QuizResults {...defaultProps} result={highResult} />);
    const messageElement = screen.getByText("Excellent!");
    expect(messageElement).toHaveClass("text-green-600");
  });

  it("applies blue text color for scores >= 70% and < 90%", () => {
    const goodResult = createMockResult(7, 10); // 70%
    render(<QuizResults {...defaultProps} result={goodResult} />);
    const messageElement = screen.getByText("Great job!");
    expect(messageElement).toHaveClass("text-blue-600");
  });

  it("applies yellow text color for scores >= 50% and < 70%", () => {
    const averageResult = createMockResult(5, 10); // 50%
    render(<QuizResults {...defaultProps} result={averageResult} />);
    const messageElement = screen.getByText("Good effort!");
    expect(messageElement).toHaveClass("text-yellow-600");
  });

  it("applies red text color for scores < 50%", () => {
    const lowResult = createMockResult(4, 10); // 40%
    render(<QuizResults {...defaultProps} result={lowResult} />);
    const messageElement = screen.getByText("Keep learning!");
    expect(messageElement).toHaveClass("text-red-600");
  });

  it("calls onRetry when 'Try Again' button is clicked", () => {
    render(<QuizResults {...defaultProps} />);
    fireEvent.click(screen.getByText("Try Again"));
    expect(defaultProps.onRetry).toHaveBeenCalledTimes(1);
  });

  it("calls onNewQuiz when 'Create New Quiz' button is clicked", () => {
    render(<QuizResults {...defaultProps} />);
    fireEvent.click(screen.getByText("Create New Quiz"));
    expect(defaultProps.onNewQuiz).toHaveBeenCalledTimes(1);
  });

  it("renders the circular progress indicator with correct percentage", () => {
    render(<QuizResults {...defaultProps} />);
    const progressPath = document.querySelector("path:nth-of-type(2)");
    expect(progressPath).toHaveAttribute("stroke-dasharray", "60, 100");
  });
});
