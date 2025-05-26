// import { useAuth } from "../context/AuthContext";
import CreateQuiz from "../components/CreateQuiz";

export default function HomePage() {
  // const { user } = useAuth();

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

      <CreateQuiz />
    </div>
  );
}
