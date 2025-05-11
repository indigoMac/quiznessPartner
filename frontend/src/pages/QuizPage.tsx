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
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </Layout>
    );
  }

  if (isError || !quiz) {
    return (
      <Layout>
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-red-600 mb-4">
            Error Loading Quiz
          </h2>
          <p className="text-gray-700 mb-6">
            We couldn't load the quiz you requested. It may have been deleted or
            there might be a temporary issue.
          </p>
          <Button onClick={() => (window.location.href = "/")}>
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
        <div className="max-w-3xl mx-auto">
          <QuizResults
            result={quizResult}
            onRetry={handleRetry}
            onNewQuiz={handleNewQuiz}
          />

          <div className="mt-8">
            <h3 className="text-xl font-bold mb-4">Review Your Answers</h3>
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
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-3xl mx-auto">
        <div className="bg-white shadow-md rounded-lg overflow-hidden mb-6">
          <div className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">
                {quiz.topic ? `Quiz: ${quiz.topic}` : "Quiz"}
              </h2>
              <div className="text-sm font-medium text-gray-600">
                Question {currentQuestion + 1} of {quiz.questions.length}
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full h-2 bg-gray-200 rounded-full mb-8">
              <div
                className="h-full bg-blue-500 rounded-full"
                style={{
                  width: `${
                    ((currentQuestion + 1) / quiz.questions.length) * 100
                  }%`,
                }}
              ></div>
            </div>

            {/* Current question */}
            {quiz.questions[currentQuestion] && (
              <QuizQuestion
                question={quiz.questions[currentQuestion]}
                questionNumber={currentQuestion + 1}
                selectedAnswer={answers[currentQuestion]}
                onSelectAnswer={handleSelectAnswer}
              />
            )}

            {/* Navigation buttons */}
            <div className="flex justify-between mt-6">
              <Button
                variant="outline"
                onClick={handlePreviousQuestion}
                disabled={currentQuestion === 0}
              >
                Previous
              </Button>

              {currentQuestion < quiz.questions.length - 1 ? (
                <Button
                  onClick={handleNextQuestion}
                  disabled={answers[currentQuestion] === null}
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
