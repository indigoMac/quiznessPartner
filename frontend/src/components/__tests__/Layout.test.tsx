import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Layout from "../Layout";

// Create a wrapper with necessary providers
const queryClient = new QueryClient();
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

// Mock values that will be updated in each test
let mockUser: { email: string } | null = null;
const mockLogout = vi.fn();

// Mock the auth context
vi.mock("../../context/AuthContext", () => ({
  useAuth: () => ({
    user: mockUser,
    logout: mockLogout,
  }),
}));

describe("Layout", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    mockUser = null;
    mockLogout.mockClear();
  });

  it("renders navigation with logo", () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>,
      { wrapper }
    );

    const logo = screen.getByRole("heading", {
      name: (content) =>
        content.includes("Quizness") && content.includes("Partner"),
    });
    expect(logo).toBeInTheDocument();
  });

  it("renders child content", () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>,
      { wrapper }
    );

    expect(screen.getByText("Test Content")).toBeInTheDocument();
  });

  it("shows user navigation when authenticated", () => {
    mockUser = { email: "test@example.com" };

    render(
      <Layout>
        <div>Test Content</div>
      </Layout>,
      { wrapper }
    );

    expect(
      screen.getByRole("link", { name: /dashboard/i })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /logout/i })).toBeInTheDocument();
  });

  it("shows login/register when not authenticated", () => {
    // Ensure mockUser is null for this test
    mockUser = null;

    // Re-mock the auth context specifically for this test
    vi.mock("../../context/AuthContext", () => ({
      useAuth: () => ({
        user: null,
        logout: mockLogout,
      }),
    }));

    render(
      <Layout>
        <div>Test Content</div>
      </Layout>,
      { wrapper }
    );

    expect(screen.getByRole("link", { name: /login/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /register/i })).toBeInTheDocument();
  });

  it("handles logout", async () => {
    // Set up authenticated user
    mockUser = { email: "test@example.com" };

    // Re-mock the auth context specifically for this test
    vi.mock("../../context/AuthContext", () => ({
      useAuth: () => ({
        user: mockUser,
        logout: mockLogout,
      }),
    }));

    const user = userEvent.setup();
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>,
      { wrapper }
    );

    const logoutButton = screen.getByRole("button", { name: /logout/i });
    await user.click(logoutButton);

    expect(mockLogout).toHaveBeenCalled();
  });

  it("navigates to correct routes", async () => {
    mockUser = { email: "test@example.com" };

    const user = userEvent.setup();
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>,
      { wrapper }
    );

    const dashboardLink = screen.getByRole("link", { name: /dashboard/i });
    await user.click(dashboardLink);
    expect(window.location.pathname).toBe("/dashboard");
  });
});
