import { useState, type FC } from "react";
import { useExplainQuestion } from "../hooks/useExplainQuestion";
import Button from "./Button";

interface QuestionExplanationProps {
  quizId: number;
  questionId: number;
  selectedAnswer?: number;
}

const QuestionExplanation: FC<QuestionExplanationProps> = ({
  quizId,
  questionId,
  selectedAnswer,
}) => {
  const [open, setOpen] = useState(false);
  const {
    explanation,
    isLoading,
    error,
    requestExplanation,
    retry,
    isRequested,
  } = useExplainQuestion(quizId, questionId, selectedAnswer);

  const handleToggle = () => {
    if (!isRequested) {
      requestExplanation();
      setOpen(true);
      return;
    }
    setOpen((current) => !current);
  };

  const errorMessage =
    error instanceof Error
      ? error.message
      : "Could not load an explanation.";
  const buttonLabel =
    open && isRequested && !isLoading
      ? "Hide explanation"
      : "Explain this question";

  return (
    <div className="mt-3">
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={handleToggle}
        isLoading={isLoading && !explanation}
      >
        {buttonLabel}
      </Button>

      {open && isRequested && (
        <div
          className="mt-3 rounded-xl border border-stone-200 bg-stone-50 p-4 dark:border-stone-700 dark:bg-stone-900/60"
          data-testid="question-explanation"
        >
          <p className="page-kicker mb-2">Explanation</p>
          {isLoading && !explanation && (
            <p className="text-sm text-stone-600 dark:text-stone-400">
              Looking at the source material...
            </p>
          )}
          {error && !explanation && (
            <div>
              <p className="mb-3 text-sm text-red-700 dark:text-red-400">
                {errorMessage}
              </p>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  void retry();
                }}
              >
                Try again
              </Button>
            </div>
          )}
          {explanation && (
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-stone-700 dark:text-stone-300">
              {explanation}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default QuestionExplanation;
