import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import CreateQuiz from "../components/CreateQuiz";
import Button from "../components/Button";

export default function HomePage() {
  const { user, isLoading } = useAuth();

  return (
    <div>
      <div className="max-w-4xl mx-auto text-center mb-8">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
          Welcome to Quizness Partner
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300">
          Create engaging quizzes from your documents or text with AI assistance
        </p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div
            data-testid="loading-spinner"
            className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"
          ></div>
        </div>
      ) : user ? (
        <CreateQuiz />
      ) : (
        <div className="max-w-xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-md p-8 text-center">
          <h2 className="text-2xl font-semibold mb-3">Sign in to create quizzes</h2>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            Create an account to generate quizzes from PDFs or text, save them,
            and track your results.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link to="/register">
              <Button className="w-full sm:w-auto">Create an account</Button>
            </Link>
            <Link to="/login">
              <Button variant="secondary" className="w-full sm:w-auto">
                Log in
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
