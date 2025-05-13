import React from "react";
import type { QuizQuestion as QuizQuestionType } from "../types/api";

interface QuizQuestionProps {
  question: QuizQuestionType;
  questionNumber: number;
  selectedAnswer: number | null;
  onSelectAnswer: (index: number) => void;
  showResults?: boolean;
}

const QuizQuestion: React.FC<QuizQuestionProps> = ({
  question,
  questionNumber,
  selectedAnswer,
  onSelectAnswer,
  showResults = false,
}) => {
  const getOptionClasses = (index: number) => {
    const baseClasses =
      "border rounded-lg p-4 mb-3 transition-all duration-200 cursor-pointer hover:shadow-md";

    if (selectedAnswer === index) {
      if (showResults) {
        if (index === question.correct_answer) {
          return `${baseClasses} border-green-500 bg-green-50 dark:bg-green-900/20 dark:border-green-600`;
        } else {
          return `${baseClasses} border-red-500 bg-red-50 dark:bg-red-900/20 dark:border-red-600`;
        }
      } else {
        return `${baseClasses} border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 dark:border-indigo-600`;
      }
    } else if (showResults && index === question.correct_answer) {
      return `${baseClasses} border-green-500 bg-green-50 dark:bg-green-900/20 dark:border-green-600`;
    }

    return `${baseClasses} border-gray-200 dark:border-gray-700 dark:bg-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800`;
  };

  return (
    <div className="mb-8">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
        <span className="text-indigo-600 dark:text-indigo-400 font-bold">
          {questionNumber}.
        </span>{" "}
        {question.question}
      </h3>
      <div className="space-y-3">
        {question.options.map((option, index) => (
          <div
            key={index}
            className={getOptionClasses(index)}
            onClick={() => !showResults && onSelectAnswer(index)}
          >
            <div className="flex items-start">
              <div className="flex-shrink-0 mt-0.5">
                <div
                  className={`w-5 h-5 rounded-full border flex items-center justify-center transition-all duration-200
                  ${
                    selectedAnswer === index
                      ? showResults
                        ? index === question.correct_answer
                          ? "border-green-500 bg-green-500 dark:border-green-400 dark:bg-green-400"
                          : "border-red-500 bg-red-500 dark:border-red-400 dark:bg-red-400"
                        : "border-indigo-500 bg-indigo-500 dark:border-indigo-400 dark:bg-indigo-400"
                      : "border-gray-300 dark:border-gray-600"
                  }`}
                >
                  {selectedAnswer === index && (
                    <span className="text-white dark:text-white text-xs">
                      ✓
                    </span>
                  )}
                </div>
              </div>
              <div className="ml-3 flex-grow">
                <p className="text-base text-gray-700 dark:text-gray-300">
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
          </div>
        ))}
      </div>
    </div>
  );
};

export default QuizQuestion;
