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
  practiceStudyTopic,
  saveStudyMaterial,
  getStudyTopic,
  loadOrCreateEpisode,
  generateStudyEpisode,
  generateStudyAudio,
} from "../api/quizApi";
import type {
  GenerateQuizForm,
  GenerateQuizFromUrlForm,
  UploadDocumentForm,
  AnswerSubmission,
  PracticeStudyTopicForm,
  SaveStudyMaterialForm,
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

export const useSaveStudyMaterial = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SaveStudyMaterialForm) => saveStudyMaterial(data),
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

export const usePracticeStudyTopic = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PracticeStudyTopicForm) => practiceStudyTopic(data),
    onSuccess: (_quiz, variables) => {
      queryClient.invalidateQueries({ queryKey: ["my-quizzes"] });
      queryClient.invalidateQueries({
        queryKey: ["study-topic", variables.study_topic_id],
      });
    },
  });
};

export const useStudyTopic = (studyTopicId: number | null) => {
  return useQuery({
    queryKey: ["study-topic", studyTopicId],
    queryFn: () => getStudyTopic(studyTopicId!),
    enabled: !!studyTopicId,
    retry: false,
  });
};

export const useStudyEpisode = (studyTopicId: number | null) => {
  return useQuery({
    queryKey: ["study-episode", studyTopicId],
    queryFn: () => loadOrCreateEpisode(studyTopicId!),
    enabled: !!studyTopicId,
    retry: false,
    refetchInterval: (query) =>
      query.state.data?.audio_status === "generating" ? 2000 : false,
  });
};

export const useGenerateStudyEpisode = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (studyTopicId: number) => generateStudyEpisode(studyTopicId),
    onSuccess: (episode) => {
      queryClient.setQueryData(
        ["study-episode", episode.study_topic_id],
        episode
      );
    },
  });
};

export const useGenerateStudyAudio = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (studyTopicId: number) => generateStudyAudio(studyTopicId),
    onSuccess: (episode) => {
      queryClient.setQueryData(
        ["study-episode", episode.study_topic_id],
        episode
      );
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
