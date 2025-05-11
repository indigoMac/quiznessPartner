import { useMutation, useQuery } from "@tanstack/react-query";
import {
  generateQuiz,
  uploadDocument,
  getQuiz,
  submitAnswers,
  checkHealth,
} from "../api/quizApi";
import type {
  GenerateQuizForm,
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
  return useMutation({
    mutationFn: (data: GenerateQuizForm) => generateQuiz(data),
  });
};

// Hook for uploading a document
export const useUploadDocument = () => {
  return useMutation({
    mutationFn: (data: UploadDocumentForm) => uploadDocument(data),
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
  return useMutation({
    mutationFn: (data: AnswerSubmission) => submitAnswers(data),
  });
};
