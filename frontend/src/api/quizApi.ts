import axios, { AxiosHeaders } from "axios";
import API_BASE_URL from "./config";
import type {
  QuizResponse,
  AnswerSubmission,
  QuizResult,
  GenerateQuizForm,
  GenerateQuizFromUrlForm,
  UploadDocumentForm,
  QuizListResponse,
  PracticeStudyTopicForm,
  ExplainQuestionRequest,
  ExplainQuestionResponse,
  SaveStudyMaterialForm,
  StudyTopicDetail,
  Episode,
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

export const generateQuizFromUrl = async (
  data: GenerateQuizFromUrlForm
): Promise<QuizResponse> => {
  const response = await api.post<QuizResponse>(
    "/api/v1/generate-quiz-from-url",
    data
  );
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

  if (data.difficulty) {
    formData.append("difficulty", data.difficulty);
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

export const explainQuestion = async (
  data: ExplainQuestionRequest
): Promise<ExplainQuestionResponse> => {
  try {
    const response = await api.post<ExplainQuestionResponse>(
      `/api/v1/quiz/${data.quiz_id}/questions/${data.question_id}/explain`,
      { selected_answer: data.selected_answer }
    );
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const detail = error.response?.data?.detail;
      if (typeof detail === "string") {
        throw new Error(detail);
      }
    }
    throw error;
  }
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

export const saveStudyMaterial = async (
  data: SaveStudyMaterialForm
): Promise<StudyTopicDetail> => {
  const formData = new FormData();
  if (data.file) {
    formData.append("file", data.file);
  }
  if (data.content) {
    formData.append("content", data.content);
  }
  if (data.url) {
    formData.append("url", data.url);
  }
  if (data.topic) {
    formData.append("topic", data.topic);
  }

  const response = await api.post<StudyTopicDetail>(
    "/api/v1/study-topics",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
};

function errorDetail(error: unknown): string | null {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return null;
}

function isMissingEpisode(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 404;
}

async function readBlob(data: Blob): Promise<string> {
  if (typeof data.text === "function") return data.text();
  if (typeof data.arrayBuffer === "function") {
    const bytes = await data.arrayBuffer();
    return new TextDecoder().decode(bytes);
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(data);
  });
}

async function errorMessage(error: unknown): Promise<string | null> {
  const detail = errorDetail(error);
  if (detail) return detail;
  if (!axios.isAxiosError(error) || !(error.response?.data instanceof Blob)) {
    return null;
  }
  const raw = await readBlob(error.response.data);
  try {
    const parsed = JSON.parse(raw) as { detail?: unknown };
    if (typeof parsed.detail === "string") return parsed.detail;
  } catch {
    return null;
  }
  return null;
}

export const getStudyTopic = async (
  studyTopicId: number
): Promise<StudyTopicDetail> => {
  try {
    const response = await api.get<StudyTopicDetail>(
      `/api/v1/study-topics/${studyTopicId}`
    );
    return response.data;
  } catch (error) {
    const detail = errorDetail(error);
    if (detail) throw new Error(detail);
    throw error;
  }
};

export const getStudyEpisode = async (
  studyTopicId: number
): Promise<Episode> => {
  const response = await api.get<Episode>(
    `/api/v1/study-topics/${studyTopicId}/episode`
  );
  return response.data;
};

export const generateStudyEpisode = async (
  studyTopicId: number
): Promise<Episode> => {
  try {
    const response = await api.post<Episode>(
      `/api/v1/study-topics/${studyTopicId}/episode`
    );
    return response.data;
  } catch (error) {
    const detail = errorDetail(error);
    if (detail) throw new Error(detail);
    throw error;
  }
};

export const getEpisodeAudio = async (studyTopicId: number): Promise<Blob> => {
  try {
    const response = await api.get<Blob>(
      `/api/v1/study-topics/${studyTopicId}/episode/audio`,
      { responseType: "blob" }
    );
    return response.data;
  } catch (error) {
    const detail = await errorMessage(error);
    if (detail) throw new Error(detail);
    throw error;
  }
};

export const generateStudyAudio = async (
  studyTopicId: number
): Promise<Episode> => {
  try {
    const response = await api.post<Episode>(
      `/api/v1/study-topics/${studyTopicId}/episode/audio`
    );
    return response.data;
  } catch (error) {
    const detail = errorDetail(error);
    if (detail) throw new Error(detail);
    throw error;
  }
};

export const loadOrCreateEpisode = async (
  studyTopicId: number
): Promise<Episode> => {
  try {
    return await getStudyEpisode(studyTopicId);
  } catch (error) {
    if (isMissingEpisode(error)) {
      return generateStudyEpisode(studyTopicId);
    }
    const detail = errorDetail(error);
    if (detail) throw new Error(detail);
    throw error;
  }
};

export const practiceStudyTopic = async (
  data: PracticeStudyTopicForm
): Promise<QuizResponse> => {
  try {
    const response = await api.post<QuizResponse>(
      `/api/v1/study-topics/${data.study_topic_id}/practice`,
      {
        num_questions: data.num_questions ?? 5,
        difficulty: data.difficulty ?? "medium",
      }
    );
    return response.data;
  } catch (error) {
    const detail = errorDetail(error);
    if (detail) throw new Error(detail);
    throw error;
  }
};
