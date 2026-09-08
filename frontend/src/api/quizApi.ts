import axios, { AxiosHeaders } from "axios";
import API_BASE_URL from "./config";
import type {
  QuizResponse,
  AnswerSubmission,
  QuizResult,
  GenerateQuizForm,
  UploadDocumentForm,
  QuizListResponse,
} from "../types/api";

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    const headers = AxiosHeaders.from(config.headers);
    headers.set("Authorization", `Bearer ${token}`);
    config.headers = headers;
  }
  return config;
});

// Generate a quiz from text
export const generateQuiz = async (
  data: GenerateQuizForm
): Promise<QuizResponse> => {
  const response = await api.post<QuizResponse>("/api/v1/generate-quiz", data);
  return response.data;
};

// Upload a document for quiz generation
export const uploadDocument = async (
  data: UploadDocumentForm
): Promise<QuizResponse> => {
  const formData = new FormData();
  formData.append("file", data.file);

  if (data.topic) {
    formData.append("topic", data.topic);
  }

  if (data.num_questions) {
    formData.append("num_questions", data.num_questions.toString());
  }

  const response = await api.post<QuizResponse>(
    "/api/v1/upload-document",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
};

// Get a quiz by ID
export const getQuiz = async (quizId: string): Promise<QuizResponse> => {
  const response = await api.get<QuizResponse>(`/api/v1/quiz/${quizId}`);
  return response.data;
};

// Submit quiz answers
export const submitAnswers = async (
  data: AnswerSubmission
): Promise<QuizResult> => {
  const response = await api.post<QuizResult>("/api/v1/submit-answer", data);
  return response.data;
};

// Health check
export const checkHealth = async (): Promise<{
  status: string;
  version: string;
}> => {
  const response = await api.get<{ status: string; version: string }>(
    "/health"
  );
  return response.data;
};

export const listMyQuizzes = async (): Promise<QuizListResponse> => {
  const token = localStorage.getItem("token");
  const headers: HeadersInit = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes`, { headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const detail =
      typeof error.detail === "string" ? error.detail : "Failed to load quizzes";
    throw new Error(detail);
  }
  return response.json();
};
