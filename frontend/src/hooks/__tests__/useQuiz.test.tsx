import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

const mocks = vi.hoisted(() => ({
  token: null as string | null,
  listMyQuizzes: vi.fn(),
}));

vi.mock("../../context/AuthContext", () => ({
  useAuth: () => ({ token: mocks.token }),
}));

vi.mock("../../api/quizApi", () => ({
  generateQuiz: vi.fn(),
  generateQuizFromUrl: vi.fn(),
  uploadDocument: vi.fn(),
  getQuiz: vi.fn(),
  submitAnswers: vi.fn(),
  checkHealth: vi.fn(),
  listMyQuizzes: (...args: unknown[]) => mocks.listMyQuizzes(...args),
  practiceStudyTopic: vi.fn(),
}));

import { useMyQuizzes } from "../useQuiz";

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useMyQuizzes", () => {
  beforeEach(() => {
    mocks.token = null;
    mocks.listMyQuizzes.mockReset();
  });

  it("does not fetch quizzes when the user is logged out", () => {
    renderHook(() => useMyQuizzes(), { wrapper });
    expect(mocks.listMyQuizzes).not.toHaveBeenCalled();
  });

  it("fetches quizzes when a token is present", async () => {
    mocks.token = "test-token";
    mocks.listMyQuizzes.mockResolvedValue({
      quizzes: [],
      total_quizzes: 0,
      completed: 0,
    });

    renderHook(() => useMyQuizzes(), { wrapper });

    await waitFor(() => {
      expect(mocks.listMyQuizzes).toHaveBeenCalledTimes(1);
    });
  });
});
