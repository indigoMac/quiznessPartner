import { vi, describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import QuizPage from "../QuizPage";
import type { QuizResponse, QuizResult } from "../../types/api";
import type { User } from "../../types/auth";

// Mock the hooks
const mockUseAuth = vi.fn();
const mockUseGetQuiz = vi.fn();
const mockUseSubmitAnswers = vi.fn();

vi.mock("../../context/AuthContext", () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock("../../hooks/useQuiz", () => ({
  useGetQuiz: () => mockUseGetQuiz(),
  useSubmitAnswers: () => mockUseSubmitAnswers(),
}));

vi.mock("react-router-dom", () => ({
  useNavigate: vi.fn(),
  useParams: () => ({ id: "123" }),
  BrowserRouter: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

describe("QuizPage", () => {
  const mockQuizData: QuizResponse = {
    id: "123",
    title: "Test Quiz",
    questions: [
      {
        id: 1,
        question: "What is the capital of France?",
        options: ["London", "Paris", "Berlin", "Madrid"],
        correct_answer: 1,
      },
    ],
  };

  const mockUser: User = {
    id: "1",
    email: "test@test.com",
  };

  const mockQuizResult: QuizResult = {
    quiz_id: 123,
    score: 1,
    total: 1,
    answers: [1],
    correct_answers: [1],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      token: "mock-token",
      login: vi.fn(),
      logout: vi.fn(),
    });
    mockUseGetQuiz.mockReturnValue({
      data: mockQuizData,
      isLoading: false,
      error: null,
      isError: false,
      isPending: false,
      isLoadingError: false,
      isRefetchError: false,
      status: "success",
    });
    mockUseSubmitAnswers.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(mockQuizResult),
      isPending: false,
      isError: false,
      error: null,
      mutate: vi.fn(),
    });
  });

  it("renders quiz title and questions", () => {
    render(<QuizPage />, { wrapper });

    expect(screen.getByText("Test Quiz")).toBeInTheDocument();
    expect(
      screen.getByText("What is the capital of France?")
    ).toBeInTheDocument();
    expect(screen.getByText("London")).toBeInTheDocument();
    expect(screen.getByText("Paris")).toBeInTheDocument();
    expect(screen.getByText("Berlin")).toBeInTheDocument();
    expect(screen.getByText("Madrid")).toBeInTheDocument();
  });

  it("allows selecting answers", async () => {
    const user = userEvent.setup();
    render(<QuizPage />, { wrapper });

    const parisOption = screen.getByText("Paris");
    await user.click(parisOption);

    expect(parisOption.closest("button")).toHaveClass("bg-indigo-50");
  });

  it("enables submit button when all questions are answered", async () => {
    const user = userEvent.setup();
    render(<QuizPage />, { wrapper });

    const submitButton = screen.getByText(/submit answers/i).closest("button");
    expect(submitButton).toBeDisabled();

    const parisOption = screen.getByText("Paris");
    await user.click(parisOption);

    expect(submitButton).not.toBeDisabled();
  });

  it("shows quiz results after submission", async () => {
    const user = userEvent.setup();
    render(<QuizPage />, { wrapper });

    const parisOption = screen.getByText("Paris");
    await user.click(parisOption);

    const submitButton = screen.getByText(/submit answers/i);
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("100%")).toBeInTheDocument();
      expect(screen.getByText(/you scored 1 out of 1/i)).toBeInTheDocument();
    });
  });

  it("shows loading state", () => {
    mockUseGetQuiz.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      isError: false,
      isPending: true,
      isLoadingError: false,
      isRefetchError: false,
      status: "loading",
    });

    render(<QuizPage />, { wrapper });

    const loadingSpinner = screen.getByTestId("loading-spinner");
    expect(loadingSpinner).toBeInTheDocument();
  });

  it("shows error state", () => {
    mockUseGetQuiz.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Failed to load quiz"),
      isError: true,
      isPending: false,
      isLoadingError: true,
      isRefetchError: false,
      status: "error",
    });

    render(<QuizPage />, { wrapper });

    expect(screen.getByText("Error Loading Quiz")).toBeInTheDocument();
  });
});
