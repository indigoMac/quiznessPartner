import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { act } from "react";

const mocks = vi.hoisted(() => ({
  explainQuestion: vi.fn(),
}));

vi.mock("../../api/quizApi", () => ({
  explainQuestion: (...args: unknown[]) => mocks.explainQuestion(...args),
}));

import { useExplainQuestion } from "../useExplainQuestion";

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useExplainQuestion", () => {
  beforeEach(() => {
    mocks.explainQuestion.mockReset();
  });

  it("does not fetch until an explanation is requested", () => {
    renderHook(() => useExplainQuestion(1, 2, 0), { wrapper });
    expect(mocks.explainQuestion).not.toHaveBeenCalled();
  });

  it("fetches and caches the explanation after it is requested", async () => {
    mocks.explainQuestion.mockResolvedValue({
      explanation: "Because the source says so.",
    });

    const { result } = renderHook(() => useExplainQuestion(1, 2, 0), {
      wrapper,
    });

    act(() => {
      result.current.requestExplanation();
    });

    await waitFor(() => {
      expect(result.current.explanation).toBe("Because the source says so.");
    });
    expect(mocks.explainQuestion).toHaveBeenCalledWith({
      quiz_id: 1,
      question_id: 2,
      selected_answer: 0,
    });
  });
});
