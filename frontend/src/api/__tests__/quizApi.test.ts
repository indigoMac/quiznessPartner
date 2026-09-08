import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";

const { MockAxiosHeaders } = vi.hoisted(() => {
  class MockAxiosHeaders {
    private values: Record<string, string>;

    constructor(headers: Record<string, string> = {}) {
      this.values = { ...headers };
    }

    static from(headers?: unknown) {
      if (headers instanceof MockAxiosHeaders) {
        return headers;
      }
      return new MockAxiosHeaders((headers as Record<string, string>) || {});
    }

    set(key: string, value: string) {
      this.values[key] = value;
      return this;
    }

    get(key: string) {
      return this.values[key];
    }
  }

  return { MockAxiosHeaders };
});

vi.mock("axios", () => {
  const mockPost = vi.fn().mockResolvedValue({ data: { title: "Mock Quiz" } });
  const mockGet = vi.fn().mockResolvedValue({ data: { title: "Mock Quiz" } });
  const mockUse = vi.fn().mockImplementation((interceptor) => interceptor);

  return {
    AxiosHeaders: MockAxiosHeaders,
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
  generateQuizFromUrl,
  uploadDocument,
  getQuiz,
  submitAnswers,
  checkHealth,
  listMyQuizzes,
} from "../quizApi";
import API_BASE_URL from "../config";

describe("Quiz API", () => {
  beforeEach(async () => {
    localStorage.clear();
    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    (instance.post as unknown as { mockClear: () => void }).mockClear();
    (instance.get as unknown as { mockClear: () => void }).mockClear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("attaches Authorization via AxiosHeaders on axios requests", async () => {
    localStorage.setItem("token", "test-token");
    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    const interceptor = (
      instance.interceptors.request.use as ReturnType<typeof vi.fn>
    ).mock.calls[0][0];

    const result = interceptor({ headers: {} });
    expect(result.headers.get("Authorization")).toBe("Bearer test-token");
  });

  it("lists quizzes with the stored bearer token", async () => {
    localStorage.setItem("token", "test-token");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ quizzes: [], total_quizzes: 0, completed: 0 }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await listMyQuizzes();

    expect(fetchMock).toHaveBeenCalledWith(`${API_BASE_URL}/api/v1/quizzes`, {
      headers: { Authorization: "Bearer test-token" },
    });
  });

  it("throws when listing quizzes fails", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "Could not validate credentials" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(listMyQuizzes()).rejects.toThrow("Could not validate credentials");
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

  it("generates a quiz from a URL", async () => {
    const data = {
      url: "https://example.com/article",
      topic: "Biology",
      num_questions: 5,
    };
    await generateQuizFromUrl(data);

    const mockAxios = (await import("axios")).default;
    const instance = mockAxios.create();
    const postCall = instance.post as unknown as jest.Mock;
    const [url, payload] = postCall.mock.calls[0];
    expect(url).toBe("/api/v1/generate-quiz-from-url");
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
