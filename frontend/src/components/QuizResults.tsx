import type { FC } from "react";
import Button from "./Button";

interface QuizResultsProps {
  result: {
    score: number;
    total: number;
  };
  onNewQuiz: () => void;
  onRetry: () => void;
  onPracticeAgain?: () => void;
  isPracticing?: boolean;
}

const QuizResults: FC<QuizResultsProps> = ({
  result,
  onNewQuiz,
  onRetry,
  onPracticeAgain,
  isPracticing = false,
}) => {
  const percentage = Math.round((result.score / result.total) * 100);

  const getScoreMessage = () => {
    if (percentage >= 90) {
      return { message: "Excellent!", color: "text-teal-800 dark:text-teal-300" };
    } else if (percentage >= 70) {
      return { message: "Great job!", color: "text-teal-700 dark:text-teal-400" };
    } else if (percentage >= 50) {
      return { message: "Good effort!", color: "text-amber-700 dark:text-amber-400" };
    } else {
      return { message: "Keep learning!", color: "text-red-700 dark:text-red-400" };
    }
  };

  const { message, color } = getScoreMessage();
  const ringColor =
    percentage >= 70
      ? "text-teal-700"
      : percentage >= 50
        ? "text-amber-600"
        : "text-red-600";

  return (
    <div className="flex flex-col items-center gap-6 p-6 sm:p-8 text-center border-t border-stone-200 dark:border-stone-800 mt-8">
      <div className="relative inline-flex">
        <svg className="w-32 h-32 transform -rotate-90" aria-hidden="true">
          <circle
            className="text-stone-200 dark:text-stone-700"
            strokeWidth="8"
            stroke="currentColor"
            fill="transparent"
            r="56"
            cx="64"
            cy="64"
          />
          <circle
            className={ringColor}
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
          className={`absolute inset-0 flex items-center justify-center font-display text-3xl font-semibold ${color}`}
        >
          {`${percentage}%`}
        </span>
      </div>

      <h2 className={`font-display text-2xl font-semibold ${color}`}>{message}</h2>

      <p className="text-lg text-stone-700 dark:text-stone-300">
        You scored {result.score} out of {result.total} questions correctly.
      </p>

      <div className="flex w-full flex-col sm:flex-row sm:flex-wrap justify-center gap-3">
        <Button onClick={onRetry} className="w-full sm:w-auto">
          Try Again
        </Button>
        {onPracticeAgain && (
          <Button
            variant="secondary"
            onClick={onPracticeAgain}
            isLoading={isPracticing}
            className="w-full sm:w-auto"
          >
            New quiz on this topic
          </Button>
        )}
        <Button variant="outline" onClick={onNewQuiz} className="w-full sm:w-auto">
          Create New Quiz
        </Button>
      </div>
    </div>
  );
};

export default QuizResults;
