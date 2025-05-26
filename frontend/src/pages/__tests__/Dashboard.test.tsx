import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Dashboard from "../Dashboard";

// Mock the auth context
vi.mock("../../context/AuthContext", () => ({
  useAuth: () => ({
    user: { email: "test@example.com" },
  }),
}));

// Create a wrapper with necessary providers
const queryClient = new QueryClient();
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

describe("Dashboard", () => {
  it("renders welcome message with user email", () => {
    render(<Dashboard />, { wrapper });
    expect(screen.getByText(/welcome, test@example.com!/i)).toBeInTheDocument();
  });

  it("renders create quiz button", () => {
    render(<Dashboard />, { wrapper });
    const createQuizButton = screen.getByRole("link", {
      name: /create new quiz/i,
    });
    expect(createQuizButton).toHaveAttribute("href", "/quiz/new");
  });

  it("renders quick stats section", () => {
    render(<Dashboard />, { wrapper });
    expect(screen.getByText("Quick Stats")).toBeInTheDocument();
    expect(screen.getByText("Total Quizzes")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
  });

  it("renders quick actions section", () => {
    render(<Dashboard />, { wrapper });
    expect(screen.getByText("Quick Actions")).toBeInTheDocument();

    const createQuizLink = screen.getByRole("link", { name: /create quiz/i });
    expect(createQuizLink).toHaveAttribute("href", "/quiz/new");

    const viewProfileLink = screen.getByRole("link", { name: /view profile/i });
    expect(viewProfileLink).toHaveAttribute("href", "/profile");
  });

  it("shows empty state for recent quizzes", () => {
    render(<Dashboard />, { wrapper });
    expect(screen.getByText("No quizzes created yet.")).toBeInTheDocument();
  });
});
