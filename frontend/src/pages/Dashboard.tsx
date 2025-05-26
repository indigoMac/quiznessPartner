import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Button from "../components/Button";

export default function Dashboard() {
  const { user } = useAuth();

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
        <div className="space-y-4">
          {/* TODO: Add quiz list */}
          <p className="text-gray-600 dark:text-gray-300 italic">
            No quizzes created yet.
          </p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Quick Stats</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-gray-600 dark:text-gray-400">Total Quizzes</p>
              <p className="text-2xl font-bold">0</p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Completed</p>
              <p className="text-2xl font-bold">0</p>
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
