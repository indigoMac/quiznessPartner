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
      "border rounded-md p-4 mb-2 transition-colors cursor-pointer hover:bg-gray-50";

    if (selectedAnswer === index) {
      if (showResults) {
        if (index === question.correct_answer) {
          return `${baseClasses} border-green-500 bg-green-50`;
        } else {
          return `${baseClasses} border-red-500 bg-red-50`;
        }
      } else {
        return `${baseClasses} border-blue-500 bg-blue-50`;
      }
    } else if (showResults && index === question.correct_answer) {
      return `${baseClasses} border-green-500 bg-green-50`;
    }

    return `${baseClasses} border-gray-200`;
  };

  return (
    <div className="mb-8">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        {questionNumber}. {question.question}
      </h3>
      <div className="space-y-2">
        {question.options.map((option, index) => (
          <div
            key={index}
            className={getOptionClasses(index)}
            onClick={() => !showResults && onSelectAnswer(index)}
          >
            <div className="flex items-start">
              <div className="flex-shrink-0 mt-0.5">
                <div
                  className={`w-5 h-5 rounded-full border flex items-center justify-center
                  ${
                    selectedAnswer === index
                      ? "border-blue-500 bg-blue-500"
                      : "border-gray-300"
                  }`}
                >
                  {selectedAnswer === index && (
                    <span className="text-white text-xs">✓</span>
                  )}
                </div>
              </div>
              <div className="ml-3">
                <p className="text-base text-gray-700">{option}</p>
              </div>
              {showResults && index === question.correct_answer && (
                <div className="ml-auto">
                  <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                    Correct
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
