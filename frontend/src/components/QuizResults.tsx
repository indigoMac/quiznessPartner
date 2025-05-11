import React from "react";
import type { QuizResult } from "../types/api";
import Button from "./Button";

interface QuizResultsProps {
  result: QuizResult;
  onRetry: () => void;
  onNewQuiz: () => void;
}

const QuizResults: React.FC<QuizResultsProps> = ({
  result,
  onRetry,
  onNewQuiz,
}) => {
  const percentage = Math.round((result.score / result.total) * 100);

  const getResultMessage = () => {
    if (percentage >= 90) return "Excellent!";
    if (percentage >= 70) return "Great job!";
    if (percentage >= 50) return "Good effort!";
    return "Keep learning!";
  };

  const getResultClass = () => {
    if (percentage >= 90) return "text-green-600";
    if (percentage >= 70) return "text-blue-600";
    if (percentage >= 50) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">
        Your Quiz Results
      </h2>

      <div className="flex flex-col items-center mb-8">
        <div className="relative w-32 h-32 flex items-center justify-center mb-4">
          <svg viewBox="0 0 36 36" className="w-full h-full">
            <path
              className="stroke-current text-gray-200"
              strokeWidth="3"
              fill="none"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              className={`stroke-current ${getResultClass()}`}
              strokeWidth="3"
              strokeLinecap="round"
              fill="none"
              strokeDasharray={`${percentage}, 100`}
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <div className="absolute text-3xl font-bold">{percentage}%</div>
        </div>
        <h3 className={`text-xl font-bold ${getResultClass()}`}>
          {getResultMessage()}
        </h3>
        <p className="text-gray-600 mt-2">
          You scored {result.score} out of {result.total} questions correctly.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row justify-center gap-4">
        <Button onClick={onRetry} variant="outline">
          Try Again
        </Button>
        <Button onClick={onNewQuiz} variant="primary">
          Create New Quiz
        </Button>
      </div>
    </div>
  );
};

export default QuizResults;
