import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import HomePage from "../HomePage";
import { useAuth } from "../../context/AuthContext";

vi.mock("../../components/CreateQuiz", () => ({
  default: () => (
    <div data-testid="mock-create-quiz">Create Quiz Component</div>
  ),
}));

vi.mock("../../context/AuthContext", () => ({
  useAuth: vi.fn(),
}));

const queryClient = new QueryClient();
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

describe("HomePage", () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      token: null,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });
  });

  it("renders welcome message", () => {
    render(<HomePage />, { wrapper });

    expect(screen.getByText("Welcome to Quizness Partner")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Create engaging quizzes from your documents or text with AI assistance"
      )
    ).toBeInTheDocument();
  });

  it("asks guests to sign in instead of showing the creator", () => {
    render(<HomePage />, { wrapper });

    expect(screen.queryByTestId("mock-create-quiz")).not.toBeInTheDocument();
    expect(screen.getByText("Sign in to create quizzes")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /create an account/i })
    ).toHaveAttribute("href", "/register");
    expect(screen.getByRole("link", { name: /log in/i })).toHaveAttribute(
      "href",
      "/login"
    );
  });

  it("renders CreateQuiz for authenticated users", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 1, email: "test@example.com" },
      token: "token",
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    render(<HomePage />, { wrapper });

    expect(screen.getByTestId("mock-create-quiz")).toBeInTheDocument();
  });
});
