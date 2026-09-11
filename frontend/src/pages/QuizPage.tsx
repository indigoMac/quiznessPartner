import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useGetQuiz, usePracticeStudyTopic, useSubmitAnswers } from "../hooks/useQuiz";
import Button from "../components/Button";
import QuizQuestion from "../components/QuizQuestion";
import QuizResults from "../components/QuizResults";
import type { QuizResult } from "../types/api";

const QuizPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [selectedAnswers, setSelectedAnswers] = useState<
    Record<string, number>
  >({});
  const [submitted, setSubmitted] = useState(false);
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);

  const { data: quiz, isLoading, error } = useGetQuiz(id || null);
  const submitMutation = useSubmitAnswers();
  const practiceMutation = usePracticeStudyTopic();

  useEffect(() => {
    setSelectedAnswers({});
    setSubmitted(false);
    setQuizResult(null);
  }, [id]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div
          data-testid="loading-spinner"
          className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-teal-700"
        ></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="font-display text-2xl font-semibold text-red-700 mb-4">
          Error Loading Quiz
        </h2>
        <p className="text-stone-600 dark:text-stone-400 mb-6">
          {error instanceof Error ? error.message : "Failed to load quiz"}
        </p>
        <Button onClick={() => navigate("/")} className="mx-auto">
          Return Home
        </Button>
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="text-center py-12">
        <h2 className="font-display text-2xl font-semibold text-stone-800 dark:text-stone-200 mb-4">
          Quiz Not Found
        </h2>
        <p className="text-stone-600 dark:text-stone-400 mb-6">
          The quiz you're looking for doesn't exist or has been removed.
        </p>
        <Button onClick={() => navigate("/")} className="mx-auto">
          Return Home
        </Button>
      </div>
    );
  }

  const transformedQuestions = quiz.questions.map((q) => ({
    ...q,
    question: q.question || "Question not available",
  }));

  const handleAnswerSelect = (questionId: number, answerIndex: number) => {
    if (questionId === undefined || questionId === null) {
      console.error("Invalid question ID:", questionId);
      return;
    }

    const questionIdStr = String(questionId);

    setSelectedAnswers((prev) => ({
      ...prev,
      [questionIdStr]: answerIndex,
    }));
  };

  const handleSubmit = async () => {
    if (!id || !quiz) return;

    try {
      const quizId = parseInt(quiz.id, 10);

      const answers = transformedQuestions
        .filter((question) => question && question.id !== undefined)
        .map((question) => selectedAnswers[String(question.id)]);

      const result = await submitMutation.mutateAsync({
        quiz_id: quizId,
        answers,
      });

      setQuizResult(result);
      setSubmitted(true);
    } catch (error) {
      console.error("Error submitting answers:", error);
    }
  };

  const handleNewQuiz = () => {
    navigate("/");
  };

  const handlePracticeAgain = async () => {
    if (!quiz?.study_topic_id) return;
    try {
      const result = await practiceMutation.mutateAsync({
        study_topic_id: quiz.study_topic_id,
        num_questions: quiz.questions.length || 5,
      });
      navigate(`/quiz/${result.id}`);
    } catch (practiceError) {
      console.error("Error generating a new quiz on this topic:", practiceError);
    }
  };

  const handleRetry = () => {
    setSelectedAnswers({});
    setSubmitted(false);
    setQuizResult(null);
    window.scrollTo(0, 0);
  };

  const allQuestionsAnswered = transformedQuestions.every((q) => {
    if (!q || q.id === undefined) return false;
    const questionIdStr = String(q.id);
    return selectedAnswers[questionIdStr] !== undefined;
  });

  const answeredCount = Object.keys(selectedAnswers).length;
  const totalQuestions = transformedQuestions.length;
  const progressPercent =
    totalQuestions === 0 ? 0 : Math.round((answeredCount / totalQuestions) * 100);

  return (
    <div className="mx-auto max-w-3xl">
      <div className="card p-5 sm:p-6">
        <div className="flex flex-col gap-4 mb-6 sm:flex-row sm:items-start sm:justify-between">
          <div>
            {quiz.topic && <p className="page-kicker mb-2">{quiz.topic}</p>}
            <h1 className="font-display text-2xl font-semibold text-stone-900 dark:text-stone-100">
              {quiz.title || "Quiz"}
            </h1>
          </div>
          {quiz.study_topic_id && (
            <Button
              variant="secondary"
              onClick={handlePracticeAgain}
              isLoading={practiceMutation.isPending}
              className="w-full sm:w-auto"
            >
              New quiz on this topic
            </Button>
          )}
        </div>

        {!submitted && (
          <div className="mb-6">
            <div className="mb-2 flex items-center justify-between text-sm text-stone-600 dark:text-stone-400">
              <span>
                {answeredCount} of {totalQuestions} answered
              </span>
              <span>{progressPercent}%</span>
            </div>
            <div
              className="h-1.5 overflow-hidden rounded-full bg-stone-200 dark:bg-stone-700"
              role="progressbar"
              aria-valuenow={progressPercent}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className="h-full rounded-full bg-teal-800 transition-all dark:bg-teal-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        )}

        <div className="space-y-8">
          {transformedQuestions.map((question, index) => {
            if (!question || question.id === undefined) return null;
            const questionIdStr = String(question.id);

            return (
              <QuizQuestion
                key={questionIdStr}
                question={question}
                questionNumber={index + 1}
                selectedAnswer={selectedAnswers[questionIdStr]}
                onSelectAnswer={(answerIndex: number) =>
                  handleAnswerSelect(question.id, answerIndex)
                }
                showResults={submitted}
              />
            );
          })}
        </div>

        {!submitted && (
          <div className="sticky bottom-0 -mx-5 mt-8 border-t border-stone-200 bg-white/95 px-5 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] backdrop-blur dark:border-stone-800 dark:bg-stone-900/95 sm:static sm:mx-0 sm:border-0 sm:bg-transparent sm:px-0 sm:py-0 sm:pb-0 sm:backdrop-blur-none dark:sm:bg-transparent">
            <Button
              onClick={handleSubmit}
              disabled={!allQuestionsAnswered || submitMutation.isPending}
              isLoading={submitMutation.isPending}
              className="w-full"
            >
              Submit Answers
            </Button>
          </div>
        )}

        {submitted && quizResult && (
          <QuizResults
            result={quizResult}
            onNewQuiz={handleNewQuiz}
            onRetry={handleRetry}
            onPracticeAgain={
              quiz.study_topic_id ? handlePracticeAgain : undefined
            }
            isPracticing={practiceMutation.isPending}
          />
        )}
      </div>
    </div>
  );
};

export default QuizPage;
