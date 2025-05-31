import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useGetQuiz, useSubmitAnswers } from "../hooks/useQuiz";
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

  // Debug quiz data
  // useEffect(() => {
  //   if (quiz) {
  //     console.log("Full quiz response:", quiz);
  //     console.log("Quiz data structure:", {
  //       id: quiz.id,
  //       title: quiz.title,
  //       topic: quiz.topic,
  //       questions: quiz.questions.map((q) => ({
  //         id: q.id,
  //         question: q.question,
  //         options: q.options,
  //         correct_answer: q.correct_answer,
  //       })),
  //     });
  //   }
  // }, [quiz]);

  // Debug selected answers
  // useEffect(() => {
  //   console.log("Selected answers:", selectedAnswers);
  // }, [selectedAnswers]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div
          data-testid="loading-spinner"
          className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"
        ></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold text-red-600 mb-4">
          Error Loading Quiz
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
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
        <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-200 mb-4">
          Quiz Not Found
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          The quiz you're looking for doesn't exist or has been removed.
        </p>
        <Button onClick={() => navigate("/")} className="mx-auto">
          Return Home
        </Button>
      </div>
    );
  }

  // Transform questions to match frontend structure
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
    // console.log("Selecting answer for question:", {
    //   questionId: questionIdStr,
    //   answerIndex,
    // });

    setSelectedAnswers((prev) => {
      const next = {
        ...prev,
        [questionIdStr]: answerIndex,
      };
      // console.log("Previous state:", prev);
      // console.log("Next state:", next);
      return next;
    });
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

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-soft p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
          {quiz.title || "Quiz"}
        </h1>

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
          <div className="mt-8">
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
          />
        )}
      </div>
    </div>
  );
};

export default QuizPage;
