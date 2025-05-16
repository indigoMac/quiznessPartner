import { describe, it, expect, vi, beforeEach } from "vitest";
import axios from "axios";
import {
  generateQuiz,
  uploadDocument,
  getQuiz,
  submitAnswers,
  checkHealth,
} from "../quizApi";
import type {
  QuizResponse,
  QuizResult,
  GenerateQuizForm,
  UploadDocumentForm,
} from "../../types/api";

// Mock axios properly
vi.mock("axios", () => {
  const mockPost = vi.fn().mockResolvedValue({ data: {} });
  const mockGet = vi.fn().mockResolvedValue({ data: {} });

  return {
    default: {
      create: vi.fn(() => ({
        post: mockPost,
        get: mockGet,
      })),
    },
  };
});

describe("Quiz API", () => {
  // Get the mocked axios instance
  const mockAxiosInstance = {
    post: (axios.create() as any).post,
    get: (axios.create() as any).get,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockAxiosInstance.post.mockClear();
    mockAxiosInstance.get.mockClear();
  });

  describe("generateQuiz", () => {
    it("should call the correct endpoint with data", async () => {
      const mockData: GenerateQuizForm = {
        content: "Test content",
        topic: "Test topic",
        num_questions: 5,
      };

      const mockResponse: QuizResponse = {
        id: "123",
        questions: [
          {
            question: "Test question?",
            options: ["A", "B", "C", "D"],
            correct_answer: 0,
          },
        ],
        topic: "Test topic",
      };

      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await generateQuiz(mockData);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        "/api/v1/generate-quiz",
        mockData
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("uploadDocument", () => {
    it("should call the correct endpoint with FormData", async () => {
      const file = new File(["test"], "test.txt", { type: "text/plain" });
      const mockData: UploadDocumentForm = {
        file,
        topic: "Test topic",
        num_questions: 5,
      };

      const mockResponse: QuizResponse = {
        id: "123",
        questions: [
          {
            question: "Test question?",
            options: ["A", "B", "C", "D"],
            correct_answer: 0,
          },
        ],
        topic: "Test topic",
      };

      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await uploadDocument(mockData);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        "/api/v1/upload-document",
        expect.any(FormData),
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getQuiz", () => {
    it("should call the correct endpoint with quiz ID", async () => {
      const quizId = "123";
      const mockResponse: QuizResponse = {
        id: "123",
        questions: [
          {
            question: "Test question?",
            options: ["A", "B", "C", "D"],
            correct_answer: 0,
          },
        ],
        topic: "Test topic",
      };

      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResponse });

      const result = await getQuiz(quizId);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        `/api/v1/quiz/${quizId}`
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("submitAnswers", () => {
    it("should call the correct endpoint with answer data", async () => {
      const mockData = {
        quiz_id: 123,
        answers: [0, 1, 2],
      };

      const mockResponse: QuizResult = {
        quiz_id: 123,
        score: 2,
        total: 3,
        answers: [0, 1, 2],
        correct_answers: [0, 1, 0],
      };

      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await submitAnswers(mockData);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        "/api/v1/submit-answer",
        mockData
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("checkHealth", () => {
    it("should call the health endpoint", async () => {
      const mockResponse = {
        status: "ok",
        version: "1.0.0",
      };

      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResponse });

      const result = await checkHealth();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith("/health");
      expect(result).toEqual(mockResponse);
    });
  });
});
