import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { explainQuestion } from "../api/quizApi";

export const useExplainQuestion = (
  quizId: number | null,
  questionId: number | null,
  selectedAnswer?: number
) => {
  const [requested, setRequested] = useState(false);

  const query = useQuery({
    queryKey: ["question-explanation", quizId, questionId, selectedAnswer],
    queryFn: () =>
      explainQuestion({
        quiz_id: quizId!,
        question_id: questionId!,
        selected_answer: selectedAnswer,
      }),
    enabled: requested && quizId != null && questionId != null,
    staleTime: Infinity,
    retry: false,
  });

  const requestExplanation = useCallback(() => {
    setRequested(true);
  }, []);

  return {
    explanation: query.data?.explanation,
    isLoading: query.isFetching,
    error: query.error,
    requestExplanation,
    retry: query.refetch,
    isRequested: requested,
  };
};
