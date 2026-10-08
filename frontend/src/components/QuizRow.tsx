import { Link } from "react-router-dom";
import { formatQuizDifficulty, type QuizSummary } from "../types/api";

function formatDate(value?: string | null) {
  if (!value) return "Unknown date";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Unknown date";
  return parsed.toLocaleDateString();
}

export default function QuizRow({ quiz }: { quiz: QuizSummary }) {
  return (
    <li>
      <Link
        to={`/quiz/${quiz.id}`}
        className="block min-h-11 rounded-xl border border-stone-200 dark:border-stone-700 p-4 hover:border-teal-700 dark:hover:border-teal-500 transition-colors"
      >
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <p className="font-semibold">{quiz.title}</p>
            <p className="text-sm text-stone-600 dark:text-stone-400">
              {quiz.topic || "No topic"} · {quiz.question_count} questions ·{" "}
              {formatQuizDifficulty(quiz.difficulty)} · Created{" "}
              {formatDate(quiz.created_at)}
            </p>
          </div>
          <p className="text-sm text-stone-500 dark:text-stone-400 sm:whitespace-nowrap">
            {quiz.attempt_count > 0
              ? `Best score: ${quiz.best_score}`
              : "Not taken yet"}
          </p>
        </div>
      </Link>
    </li>
  );
}
