import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../context/AuthContext";
import {
  generateQuiz,
  generateQuizFromUrl,
  uploadDocument,
  getQuiz,
  submitAnswers,
  checkHealth,
  listMyQuizzes,
} from "../api/quizApi";
import type {
  GenerateQuizForm,
  GenerateQuizFromUrlForm,
  UploadDocumentForm,
  AnswerSubmission,
} from "../types/api";

// Hook for checking API health
export const useHealthCheck = () => {
  return useQuery({
    queryKey: ["health"],
    queryFn: checkHealth,
  });
};

// Hook for generating a quiz from text
export const useGenerateQuiz = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GenerateQuizForm) => generateQuiz(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-quizzes"] });
    },
  });
};

export const useGenerateQuizFromUrl = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GenerateQuizFromUrlForm) => generateQuizFromUrl(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-quizzes"] });
    },
  });
};

export const useUploadDocument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UploadDocumentForm) => uploadDocument(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-quizzes"] });
    },
  });
};

// Hook for fetching a quiz by ID
export const useGetQuiz = (quizId: string | null) => {
  return useQuery({
    queryKey: ["quiz", quizId],
    queryFn: () => getQuiz(quizId!),
    enabled: !!quizId, // Only run the query if quizId exists
  });
};

// Hook for submitting quiz answers
export const useSubmitAnswers = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AnswerSubmission) => submitAnswers(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-quizzes"] });
    },
  });
};

export const useMyQuizzes = () => {
  const { token } = useAuth();
  return useQuery({
    queryKey: ["my-quizzes"],
    queryFn: listMyQuizzes,
    enabled: !!token,
  });
};
