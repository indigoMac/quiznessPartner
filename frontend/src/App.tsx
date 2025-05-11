import { useState, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import HomePage from "./pages/HomePage";
import QuizPage from "./pages/QuizPage";
import "./App.css";

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const [currentPage, setCurrentPage] = useState<string>("home");
  const [quizId, setQuizId] = useState<string | null>(null);

  // Simple client-side routing
  useEffect(() => {
    const handleRouting = () => {
      const path = window.location.pathname;
      const quizMatch = path.match(/^\/quiz\/([^/]+)/);

      if (quizMatch && quizMatch[1]) {
        setCurrentPage("quiz");
        setQuizId(quizMatch[1]);
      } else {
        setCurrentPage("home");
        setQuizId(null);
      }
    };

    // Initial routing
    handleRouting();

    // Listen for popstate events (browser back/forward buttons)
    window.addEventListener("popstate", handleRouting);

    return () => {
      window.removeEventListener("popstate", handleRouting);
    };
  }, []);

  // Render the appropriate page based on the route
  const renderPage = () => {
    switch (currentPage) {
      case "quiz":
        return quizId ? <QuizPage quizId={quizId} /> : <HomePage />;
      case "home":
      default:
        return <HomePage />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      {renderPage()}
    </QueryClientProvider>
  );
}

export default App;
