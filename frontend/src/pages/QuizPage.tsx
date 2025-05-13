import React, { useState, useEffect } from "react";
import { useGetQuiz, useSubmitAnswers } from "../hooks/useQuiz";
import Layout from "../components/Layout";
import QuizQuestion from "../components/QuizQuestion";
import QuizResults from "../components/QuizResults";
import Button from "../components/Button";
import type { QuizResult } from "../types/api";

interface QuizPageProps {
  quizId: string;
}

const QuizPage: React.FC<QuizPageProps> = ({ quizId }) => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: quiz, isLoading, isError } = useGetQuiz(quizId);
  const submitAnswersMutation = useSubmitAnswers();

  // Initialize answers array based on the number of questions
  useEffect(() => {
    if (quiz && quiz.questions) {
      setAnswers(new Array(quiz.questions.length).fill(null));
    }
  }, [quiz]);

  const handleSelectAnswer = (answer: number) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = answer;
    setAnswers(newAnswers);
  };

  const handleNextQuestion = () => {
    if (currentQuestion < (quiz?.questions.length || 0) - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const handleSubmitQuiz = async () => {
    if (!quiz) return;

    // Filter out any null answers and replace with 0 (first option)
    const validAnswers = answers.map((answer) =>
      answer === null ? 0 : answer
    );

    setIsSubmitting(true);

    try {
      const result = await submitAnswersMutation.mutateAsync({
        quiz_id: parseInt(quizId),
        answers: validAnswers,
      });

      setQuizResult(result);
    } catch (error) {
      console.error("Error submitting quiz:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = () => {
    setQuizResult(null);
    setCurrentQuestion(0);
    setAnswers(new Array(quiz?.questions.length || 0).fill(null));
  };

  const handleNewQuiz = () => {
    window.location.href = "/";
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex flex-col justify-center items-center h-64 animate-fade-in">
          <div className="w-16 h-16 relative">
            <div className="absolute top-0 w-16 h-16 rounded-full border-4 border-gray-200 dark:border-gray-700"></div>
            <div className="absolute top-0 w-16 h-16 rounded-full border-4 border-t-transparent border-l-transparent border-r-indigo-600 border-b-indigo-600 dark:border-r-indigo-400 dark:border-b-indigo-400 animate-spin"></div>
          </div>
          <p className="mt-4 text-gray-600 dark:text-gray-300 font-medium">
            Loading your quiz...
          </p>
        </div>
      </Layout>
    );
  }

  if (isError || !quiz) {
    return (
      <Layout>
        <div className="text-center py-12 animate-fade-in">
          <div className="bg-red-50 dark:bg-red-900/20 p-6 rounded-xl inline-block mb-6">
            <svg
              className="w-16 h-16 text-red-500 mx-auto"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">
            Error Loading Quiz
          </h2>
          <p className="text-gray-700 dark:text-gray-300 mb-6 max-w-md mx-auto">
            We couldn't load the quiz you requested. It may have been deleted or
            there might be a temporary issue.
          </p>
          <Button
            onClick={() => (window.location.href = "/")}
            icon={
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
            }
          >
            Back to Home
          </Button>
        </div>
      </Layout>
    );
  }

  // Show results if quiz has been submitted
  if (quizResult) {
    return (
      <Layout>
        <div className="max-w-3xl mx-auto animate-fade-in">
          <QuizResults
            result={quizResult}
            onRetry={handleRetry}
            onNewQuiz={handleNewQuiz}
          />

          <div className="mt-8 bg-white dark:bg-gray-800 shadow-soft rounded-xl overflow-hidden p-6">
            <h3 className="text-xl font-bold mb-6 text-gray-900 dark:text-white flex items-center">
              <svg
                className="w-5 h-5 mr-2 text-indigo-600 dark:text-indigo-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              Review Your Answers
            </h3>
            <div className="space-y-6">
              {quiz.questions.map((question, index) => (
                <QuizQuestion
                  key={index}
                  question={question}
                  questionNumber={index + 1}
                  selectedAnswer={answers[index]}
                  onSelectAnswer={() => {}} // Read-only in review mode
                  showResults={true}
                />
              ))}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-3xl mx-auto animate-fade-in">
        <div className="bg-white dark:bg-gray-800 shadow-soft rounded-xl overflow-hidden mb-6 transition-all duration-300">
          <div className="p-6 md:p-8">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                {quiz.topic ? `Quiz: ${quiz.topic}` : "Quiz"}
              </h2>
              <div className="bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 px-4 py-1 rounded-full text-sm font-medium">
                Question {currentQuestion + 1} of {quiz.questions.length}
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full mb-8 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-500 dark:to-purple-500 rounded-full transition-all duration-300 ease-in-out"
                style={{
                  width: `${
                    ((currentQuestion + 1) / quiz.questions.length) * 100
                  }%`,
                }}
              ></div>
            </div>

            {/* Current question */}
            <div className="transition-opacity duration-300">
              {quiz.questions[currentQuestion] && (
                <QuizQuestion
                  question={quiz.questions[currentQuestion]}
                  questionNumber={currentQuestion + 1}
                  selectedAnswer={answers[currentQuestion]}
                  onSelectAnswer={handleSelectAnswer}
                />
              )}
            </div>

            {/* Navigation buttons */}
            <div className="flex justify-between mt-8">
              <Button
                variant="outline"
                onClick={handlePreviousQuestion}
                disabled={currentQuestion === 0}
                icon={
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 19l-7-7 7-7"
                    />
                  </svg>
                }
              >
                Previous
              </Button>

              {currentQuestion < quiz.questions.length - 1 ? (
                <Button
                  onClick={handleNextQuestion}
                  disabled={answers[currentQuestion] === null}
                  icon={
                    <svg
                      className="w-5 h-5 ml-1 -mr-1"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  }
                >
                  Next
                </Button>
              ) : (
                <Button
                  onClick={handleSubmitQuiz}
                  disabled={
                    answers.some((answer) => answer === null) || isSubmitting
                  }
                  isLoading={isSubmitting}
                  variant="success"
                  icon={
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  }
                >
                  Submit Quiz
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default QuizPage;
