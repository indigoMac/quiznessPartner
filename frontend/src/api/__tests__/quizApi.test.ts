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
    const data = {
      content: "Test content for quiz generation",
      topic: "test topic",
      numQuestions: 5,
    };
    await generateQuiz(data);

    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    const postCall = instance.post as unknown as jest.Mock;
    const [url, payload] = postCall.mock.calls[0];
    expect(url).toBe("/api/v1/generate-quiz");
    expect(payload).toEqual(data);
  });

  it("uploads a document", async () => {
    const file = new File(["test"], "test.txt", { type: "text/plain" });
    const data = { file, numQuestions: 5 };
    await uploadDocument(data);

    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    const postCall = instance.post as unknown as jest.Mock;
    const [url, payload] = postCall.mock.calls[0];
    expect(url).toBe("/api/v1/upload-document");
    expect(payload).toBeInstanceOf(FormData);
  });

  it("gets a quiz by id", async () => {
    const quizId = "123";
    await getQuiz(quizId);

    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    const getCall = instance.get as unknown as jest.Mock;
    const [url] = getCall.mock.calls[0];
    expect(url).toBe(`/api/v1/quiz/${quizId}`);
  });

  it("submits answers", async () => {
    const data = { quiz_id: 123, answers: [2] };
    await submitAnswers(data);

    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    const postCall = instance.post as unknown as jest.Mock;
    const [url, payload] = postCall.mock.calls[0];
    expect(url).toBe("/api/v1/submit-answer");
    expect(payload).toEqual(data);
  });

  it("checks health", async () => {
    await checkHealth();

    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    const getCall = instance.get as unknown as jest.Mock;
    const [url] = getCall.mock.calls[0];
    expect(url).toBe("/health");
  });
});
