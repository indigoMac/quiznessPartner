import type { ChangeEvent } from "react";
import Input from "./Input";
import { QUIZ_DIFFICULTIES, type QuizDifficulty } from "../types/api";

interface QuizSettingsFieldsProps {
  numQuestions: number;
  difficulty: QuizDifficulty;
  onNumQuestionsChange: (value: number) => void;
  onDifficultyChange: (value: QuizDifficulty) => void;
}

export default function QuizSettingsFields({
  numQuestions,
  difficulty,
  onNumQuestionsChange,
  onDifficultyChange,
}: QuizSettingsFieldsProps) {
  return (
    <div className="grid gap-6 sm:grid-cols-2">
      <Input
        type="number"
        label="Number of Questions"
        value={numQuestions}
        onChange={(event: ChangeEvent<HTMLInputElement>) =>
          onNumQuestionsChange(parseInt(event.target.value, 10))
        }
        min={1}
        max={20}
      />
      <div className="w-full">
        <label
          htmlFor="quiz-difficulty"
          className="block text-sm font-medium text-stone-700 dark:text-stone-300 mb-1.5"
        >
          Difficulty
        </label>
        <select
          id="quiz-difficulty"
          value={difficulty}
          onChange={(event: ChangeEvent<HTMLSelectElement>) =>
            onDifficultyChange(event.target.value as QuizDifficulty)
          }
          className="w-full min-h-11 px-3 py-2.5 border rounded-xl shadow-sm transition-colors duration-200 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-teal-700 border-stone-300 dark:border-stone-600 dark:bg-stone-800 dark:text-white"
        >
          {QUIZ_DIFFICULTIES.map((level) => (
            <option key={level} value={level}>
              {level.charAt(0).toUpperCase() + level.slice(1)}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
