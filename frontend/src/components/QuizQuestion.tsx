import type { FC } from "react";
import type { QuizQuestion as QuizQuestionType } from "../types/api";

interface QuizQuestionProps {
  question: QuizQuestionType;
  questionNumber: number;
  selectedAnswer?: number;
  onSelectAnswer: (index: number) => void;
  showResults?: boolean;
}

const QuizQuestion: FC<QuizQuestionProps> = ({
  question,
  questionNumber,
  selectedAnswer,
  onSelectAnswer,
  showResults = false,
}) => {
  const getOptionClasses = (index: number): string => {
    const baseClasses =
      "w-full min-h-[52px] border rounded-xl p-4 mb-3 transition-colors duration-150 cursor-pointer text-left";

    if (selectedAnswer === index) {
      if (showResults) {
        if (index === question.correct_answer) {
          return `${baseClasses} border-green-500 bg-green-50 dark:bg-green-900/20 dark:border-green-600`;
        } else {
          return `${baseClasses} border-red-500 bg-red-50 dark:bg-red-900/20 dark:border-red-600`;
        }
      } else {
        return `${baseClasses} border-teal-700 bg-teal-50 dark:bg-teal-950/40 dark:border-teal-500`;
      }
    } else if (showResults && index === question.correct_answer) {
      return `${baseClasses} border-green-500 bg-green-50 dark:bg-green-900/20 dark:border-green-600`;
    }

    return `${baseClasses} border-stone-200 dark:border-stone-700 dark:bg-stone-900/40 hover:bg-stone-50 dark:hover:bg-stone-800`;
  };

  return (
    <div className="mb-8">
      <h3 className="text-lg font-medium text-stone-900 dark:text-white mb-4">
        <span className="text-teal-800 dark:text-teal-400 font-semibold">
          {questionNumber}.
        </span>{" "}
        {question.question}
      </h3>
      <div className="space-y-3">
        {question.options.map((option: string, index: number) => (
          <button
            key={index}
            type="button"
            className={getOptionClasses(index)}
            onClick={() => !showResults && onSelectAnswer(index)}
            disabled={showResults}
          >
            <div className="flex items-start">
              <div className="flex-shrink-0 mt-0.5">
                <div
                  className={`w-7 h-7 rounded-full border flex items-center justify-center text-xs font-semibold transition-all duration-200
                  ${
                    selectedAnswer === index
                      ? showResults
                        ? index === question.correct_answer
                          ? "border-green-500 bg-green-500 text-white dark:border-green-400 dark:bg-green-400"
                          : "border-red-500 bg-red-500 text-white dark:border-red-400 dark:bg-red-400"
                        : "border-teal-700 bg-teal-800 text-white dark:border-teal-400 dark:bg-teal-500"
                      : "border-stone-300 text-stone-500 dark:border-stone-600"
                  }`}
                >
                  {selectedAnswer === index ? (
                    <span className="text-white dark:text-white text-xs">
                      ✓
                    </span>
                  ) : (
                    String.fromCharCode(65 + index)
                  )}
                </div>
              </div>
              <div className="ml-3 flex-grow text-left">
                <p className="text-base text-stone-700 dark:text-stone-300">
                  {option}
                </p>
              </div>
              {showResults && index === question.correct_answer && (
                <div className="ml-2 flex-shrink-0">
                  <span className="bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 text-xs font-medium px-2.5 py-1 rounded-full flex items-center">
                    <svg
                      className="w-3 h-3 mr-1"
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
                    Correct
                  </span>
                </div>
              )}
              {showResults &&
                selectedAnswer === index &&
                index !== question.correct_answer && (
                  <div className="ml-2 flex-shrink-0">
                    <span className="bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400 text-xs font-medium px-2.5 py-1 rounded-full flex items-center">
                      <svg
                        className="w-3 h-3 mr-1"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                      Incorrect
                    </span>
                  </div>
                )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuizQuestion;
