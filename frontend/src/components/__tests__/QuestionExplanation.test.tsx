import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import QuestionExplanation from "../QuestionExplanation";

const mocks = vi.hoisted(() => ({
  explainQuestion: vi.fn(),
}));

vi.mock("../../api/quizApi", () => ({
  explainQuestion: (...args: unknown[]) => mocks.explainQuestion(...args),
}));

function renderExplanation(selectedAnswer = 0) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return render(
    <QuestionExplanation
      quizId={12}
      questionId={4}
      selectedAnswer={selectedAnswer}
    />,
    { wrapper }
  );
}

describe("QuestionExplanation", () => {
  beforeEach(() => {
    mocks.explainQuestion.mockReset();
  });

  it("loads an explanation when the button is clicked", async () => {
    const user = userEvent.setup();
    mocks.explainQuestion.mockResolvedValue({
      explanation: "Paris is the capital of France.",
    });

    renderExplanation();

    expect(
      screen.queryByTestId("question-explanation")
    ).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: /explain this question/i })
    );

    await waitFor(() => {
      expect(screen.getByTestId("question-explanation")).toHaveTextContent(
        "Paris is the capital of France."
      );
    });
    expect(mocks.explainQuestion).toHaveBeenCalledWith({
      quiz_id: 12,
      question_id: 4,
      selected_answer: 0,
    });
  });

  it("hides and shows a loaded explanation without refetching", async () => {
    const user = userEvent.setup();
    mocks.explainQuestion.mockResolvedValue({
      explanation: "Paris is the capital of France.",
    });

    renderExplanation();

    await user.click(
      screen.getByRole("button", { name: /explain this question/i })
    );
    await screen.findByText("Paris is the capital of France.");

    await user.click(
      screen.getByRole("button", { name: /hide explanation/i })
    );
    expect(
      screen.queryByTestId("question-explanation")
    ).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: /explain this question/i })
    );
    expect(screen.getByTestId("question-explanation")).toHaveTextContent(
      "Paris is the capital of France."
    );
    expect(mocks.explainQuestion).toHaveBeenCalledTimes(1);
  });

  it("shows an error and allows retry", async () => {
    const user = userEvent.setup();
    mocks.explainQuestion
      .mockRejectedValueOnce(new Error("Could not generate an explanation."))
      .mockResolvedValueOnce({
        explanation: "Paris is the capital of France.",
      });

    renderExplanation(1);

    await user.click(
      screen.getByRole("button", { name: /explain this question/i })
    );

    expect(
      await screen.findByText("Could not generate an explanation.")
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /try again/i }));

    await waitFor(() => {
      expect(screen.getByTestId("question-explanation")).toHaveTextContent(
        "Paris is the capital of France."
      );
    });
    expect(mocks.explainQuestion).toHaveBeenCalledTimes(2);
  });
});
