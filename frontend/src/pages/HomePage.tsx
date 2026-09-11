import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import CreateQuiz from "../components/CreateQuiz";
import Button from "../components/Button";

export default function HomePage() {
  const { user, isLoading } = useAuth();

  return (
    <div>
      {!user && !isLoading && (
        <div className="mx-auto mb-8 max-w-3xl text-center sm:mb-10">
          <p className="page-kicker mb-3">AI study partner</p>
          <h1 className="page-title mb-4">
            Turn notes into quizzes you'll actually finish
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-stone-600 dark:text-stone-300">
            Upload a PDF, paste text, or drop a link. Quizness Partner builds
            questions you can practice on your phone.
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div
            data-testid="loading-spinner"
            className="h-12 w-12 animate-spin rounded-full border-t-2 border-b-2 border-teal-700"
          ></div>
        </div>
      ) : user ? (
        <CreateQuiz />
      ) : (
        <div className="card mx-auto max-w-xl p-6 text-center sm:p-8">
          <h2 className="font-display text-2xl font-semibold mb-3">
            Sign in to create quizzes
          </h2>
          <p className="mb-6 text-stone-600 dark:text-stone-300">
            Create an account to generate quizzes from PDFs or text, save them,
            and track your results.
          </p>
          <div className="flex flex-col justify-center gap-3 sm:flex-row">
            <Link to="/register" className="w-full sm:w-auto">
              <Button className="w-full sm:w-auto">Create an account</Button>
            </Link>
            <Link to="/login" className="w-full sm:w-auto">
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
