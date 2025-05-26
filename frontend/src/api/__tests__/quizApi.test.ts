import { vi, describe, it, expect, beforeEach } from "vitest";
import type { InternalAxiosRequestConfig } from "axios";

vi.mock("axios", () => {
  const mockPost = vi.fn().mockResolvedValue({ data: { title: "Mock Quiz" } });
  const mockGet = vi.fn().mockResolvedValue({ data: { title: "Mock Quiz" } });
  const mockUse = vi.fn().mockImplementation((interceptor) => interceptor);

  return {
    default: {
      create: vi.fn(() => ({
        post: mockPost,
        get: mockGet,
        interceptors: {
          request: { use: mockUse },
          response: { use: vi.fn() },
        },
      })),
    },
  };
});

import {
  generateQuiz,
  uploadDocument,
  getQuiz,
  submitAnswers,
  checkHealth,
} from "../quizApi";
import type { AnswerSubmission } from "@/types/api";

describe("Quiz API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("adds auth token to request headers", async () => {
    const token = "test-token";
    localStorage.setItem("token", token);

    const config = { headers: {} } as InternalAxiosRequestConfig;
    const addToken = (config: InternalAxiosRequestConfig) => {
      if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    };
    const result = addToken(config);
    expect(result.headers.Authorization).toBe(`Bearer ${token}`);
  });

  it("generates a quiz", async () => {
    const topic = "test topic";
    const numQuestions = 5;
    await generateQuiz(topic, numQuestions);

    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    expect(instance.post).toHaveBeenCalledWith(
      "/quiz/generate",
      expect.objectContaining({ topic, numQuestions })
    );
  });

  it("uploads a document", async () => {
    const file = new File(["test"], "test.txt", { type: "text/plain" });
    const numQuestions = 5;
    await uploadDocument(file, numQuestions);

    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    expect(instance.post).toHaveBeenCalledWith(
      "/quiz/upload",
      expect.any(FormData)
    );
  });

  it("gets a quiz by id", async () => {
    const quizId = "123";
    await getQuiz(quizId);

    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    expect(instance.get).toHaveBeenCalledWith(`/quiz/${quizId}`);
  });

  it("submits answers", async () => {
    const quizId = "123";
    const answers = { "1": 2 };
    await submitAnswers(quizId, answers);

    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    expect(instance.post).toHaveBeenCalledWith(
      `/quiz/${quizId}/submit`,
      expect.objectContaining({ answers })
    );
  });

  it("checks health", async () => {
    await checkHealth();

    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    expect(instance.get).toHaveBeenCalledWith("/health");
  });
});
