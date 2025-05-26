import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import HomePage from "../HomePage";

// Mock the CreateQuiz component since it's tested separately
vi.mock("../../components/CreateQuiz", () => ({
  default: () => (
    <div data-testid="mock-create-quiz">Create Quiz Component</div>
  ),
}));

// Create a wrapper with necessary providers
const queryClient = new QueryClient();
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

describe("HomePage", () => {
  it("renders welcome message", () => {
    render(<HomePage />, { wrapper });

    expect(screen.getByText("Welcome to Quizness Partner")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Create engaging quizzes from your documents or text with AI assistance"
      )
    ).toBeInTheDocument();
  });

  it("renders CreateQuiz component", () => {
    render(<HomePage />, { wrapper });

    expect(screen.getByTestId("mock-create-quiz")).toBeInTheDocument();
  });
});
