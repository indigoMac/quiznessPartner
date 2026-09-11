import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import QuizQuestion from "../QuizQuestion";
import type { QuizQuestion as QuizQuestionType } from "../../types/api";

describe("QuizQuestion Component", () => {
  const mockQuestion: QuizQuestionType = {
    question: "What is the capital of France?",
    options: ["London", "Berlin", "Paris", "Madrid"],
    correct_answer: 2, // Paris
  };

  const defaultProps = {
    question: mockQuestion,
    questionNumber: 1,
    selectedAnswer: null,
    onSelectAnswer: vi.fn(),
    showResults: false,
  };

  it("renders the question text correctly", () => {
    render(<QuizQuestion {...defaultProps} />);
    expect(screen.getByText("1.")).toBeInTheDocument();
    expect(
      screen.getByText("What is the capital of France?")
    ).toBeInTheDocument();
  });

  it("renders all options correctly", () => {
    render(<QuizQuestion {...defaultProps} />);
    mockQuestion.options.forEach((option) => {
      expect(screen.getByText(option)).toBeInTheDocument();
    });
  });

  it("calls onSelectAnswer when an option is clicked", () => {
    const onSelectAnswer = vi.fn();
    render(<QuizQuestion {...defaultProps} onSelectAnswer={onSelectAnswer} />);

    fireEvent.click(screen.getByRole("button", { name: /paris/i }));
    expect(onSelectAnswer).toHaveBeenCalledWith(2);
  });

  it("highlights the selected answer", () => {
    render(<QuizQuestion {...defaultProps} selectedAnswer={2} />);

    expect(screen.getByRole("button", { name: /paris/i })).toHaveClass(
      "border-teal-700"
    );
  });

  it("does not call onSelectAnswer when showResults is true", () => {
    const onSelectAnswer = vi.fn();
    render(
      <QuizQuestion
        {...defaultProps}
        onSelectAnswer={onSelectAnswer}
        showResults={true}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /paris/i }));
    expect(onSelectAnswer).not.toHaveBeenCalled();
  });

  it("shows correct answer indicator when showResults is true", () => {
    render(<QuizQuestion {...defaultProps} showResults={true} />);

    expect(screen.getByText("Correct")).toBeInTheDocument();
  });

  it("shows incorrect answer indicator when wrong answer is selected and showResults is true", () => {
    render(
      <QuizQuestion
        {...defaultProps}
        selectedAnswer={0} // London (wrong answer)
        showResults={true}
      />
    );

    expect(screen.getByText("Incorrect")).toBeInTheDocument();
  });

  it("highlights correct answer in green when showResults is true", () => {
    render(<QuizQuestion {...defaultProps} showResults={true} />);

    const parisOption = screen.getByRole("button", { name: /paris/i });
    expect(parisOption).toHaveClass("border-green-500");
  });

  it("highlights selected wrong answer in red when showResults is true", () => {
    render(
      <QuizQuestion
        {...defaultProps}
        selectedAnswer={0} // London (wrong answer)
        showResults={true}
      />
    );

    const londonOption = screen.getByRole("button", { name: /london/i });
    expect(londonOption).toHaveClass("border-red-500");
  });

  it("shows checkmark for selected answer", () => {
    render(<QuizQuestion {...defaultProps} selectedAnswer={2} />);

    const checkmark = screen.getByText("✓");
    expect(checkmark).toBeInTheDocument();
  });
});
