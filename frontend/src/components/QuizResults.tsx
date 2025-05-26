import type { FC } from "react";
import Button from "./Button";

interface QuizResultsProps {
  result: {
    score: number;
    total: number;
  };
  onNewQuiz: () => void;
  onRetry: () => void;
}

const QuizResults: FC<QuizResultsProps> = ({ result, onNewQuiz, onRetry }) => {
  const percentage = Math.round((result.score / result.total) * 100);

  const getScoreMessage = () => {
    if (percentage >= 90) {
      return { message: "Excellent!", color: "text-green-600" };
    } else if (percentage >= 70) {
      return { message: "Great job!", color: "text-blue-600" };
    } else if (percentage >= 50) {
      return { message: "Good effort!", color: "text-yellow-600" };
    } else {
      return { message: "Keep learning!", color: "text-red-600" };
    }
  };

  const { message, color } = getScoreMessage();

  return (
    <div className="flex flex-col items-center gap-6 p-8 text-center">
      <div className="relative inline-flex">
        <svg className="w-32 h-32 transform -rotate-90">
          <circle
            className="text-gray-200"
            strokeWidth="8"
            stroke="currentColor"
            fill="transparent"
            r="56"
            cx="64"
            cy="64"
          />
          <circle
            className={color.replace("text", "stroke")}
            strokeWidth="8"
            strokeDasharray={`${percentage * 3.51}, 351`}
            strokeLinecap="round"
            stroke="currentColor"
            fill="transparent"
            r="56"
            cx="64"
            cy="64"
          />
        </svg>
        <span
          className={`absolute inset-0 flex items-center justify-center text-3xl font-bold ${color}`}
        >
          {`${percentage}%`}
        </span>
      </div>

      <h2 className={`text-2xl font-bold ${color}`}>{message}</h2>

      <p className="text-lg text-gray-700 dark:text-gray-300">
        You scored {result.score} out of {result.total} questions correctly.
      </p>

      <div className="flex gap-4">
        <Button onClick={onRetry}>Try Again</Button>
        <Button variant="outline" onClick={onNewQuiz}>
          Create New Quiz
        </Button>
      </div>
    </div>
  );
};

export default QuizResults;
