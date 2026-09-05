import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useMyQuizzes } from "../hooks/useQuiz";
import Button from "../components/Button";

function formatDate(value?: string | null) {
  if (!value) return "Unknown date";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Unknown date";
  return parsed.toLocaleDateString();
}

export default function Dashboard() {
  const { user } = useAuth();
  const { data, isLoading, error } = useMyQuizzes();

  const quizzes = data?.quizzes ?? [];
  const totalQuizzes = data?.total_quizzes ?? 0;
  const completed = data?.completed ?? 0;

  return (
    <div className="space-y-8">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">Welcome, {user?.email}!</h2>
        <p className="text-gray-600 dark:text-gray-300 mb-6">
          Create a new quiz or view your existing quizzes.
        </p>
        <Link to="/quiz/new">
          <Button className="w-full md:w-auto">Create New Quiz</Button>
        </Link>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4">Recent Quizzes</h3>
        {isLoading && (
          <p className="text-gray-600 dark:text-gray-300">Loading your quizzes...</p>
        )}
        {error && (
          <p className="text-red-600 dark:text-red-400">
            Could not load your quizzes. Please try again.
          </p>
        )}
        {!isLoading && !error && quizzes.length === 0 && (
          <p className="text-gray-600 dark:text-gray-300 italic">
            No quizzes created yet.
          </p>
        )}
        {!isLoading && quizzes.length > 0 && (
          <ul className="space-y-3">
            {quizzes.map((quiz) => (
              <li key={quiz.id}>
                <Link
                  to={`/quiz/${quiz.id}`}
                  className="block rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold">{quiz.title}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {quiz.topic || "No topic"} · {quiz.question_count}{" "}
                        questions · Created {formatDate(quiz.created_at)}
                      </p>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {quiz.attempt_count > 0
                        ? `Best score: ${quiz.best_score}`
                        : "Not taken yet"}
                    </p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Quick Stats</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-gray-600 dark:text-gray-400">Total Quizzes</p>
              <p className="text-2xl font-bold">{totalQuizzes}</p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Completed</p>
              <p className="text-2xl font-bold">{completed}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <Link to="/quiz/new" className="block">
              <Button variant="secondary" className="w-full text-left">
                Create Quiz
              </Button>
            </Link>
            <Link to="/profile" className="block">
              <Button variant="secondary" className="w-full text-left">
                View Profile
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
