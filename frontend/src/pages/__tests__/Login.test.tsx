import { vi, describe, it, expect } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useNavigate } from "react-router-dom";
import Login from "../Login";
import { useAuth } from "../../context/AuthContext";
import type { User } from "../../types/auth";

// Mock useAuth hook
vi.mock("../../context/AuthContext", () => ({
  useAuth: vi.fn(),
}));

// Mock react-router-dom
vi.mock("react-router-dom", () => ({
  useNavigate: vi.fn(),
  BrowserRouter: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

describe("Login", () => {
  const mockNavigate = vi.fn();
  const mockLogin = vi.fn();
  const mockUser: User = { id: "1", email: "test@example.com" };

  beforeEach(() => {
    vi.clearAllMocks();
    (useNavigate as unknown as ReturnType<typeof vi.fn>).mockReturnValue(
      mockNavigate
    );
    vi.mocked(useAuth).mockReturnValue({
      login: mockLogin,
      user: null,
      token: null,
      isLoading: false,
      logout: vi.fn(),
    });
  });

  it("renders login form", () => {
    render(<Login />);

    expect(screen.getByPlaceholderText("Email address")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Password")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in/i })
    ).toBeInTheDocument();
  });

  it("handles form submission", async () => {
    render(<Login />);

    const emailInput = screen.getByPlaceholderText("Email address");
    const passwordInput = screen.getByPlaceholderText("Password");
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "password123",
      });
    });
  });

  it("shows error message on login failure", async () => {
    const mockError = new Error("Invalid credentials");
    mockLogin.mockRejectedValueOnce(mockError);

    render(<Login />);

    const emailInput = screen.getByPlaceholderText("Email address");
    const passwordInput = screen.getByPlaceholderText("Password");
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
    });
  });

  it("redirects to dashboard on successful login", async () => {
    // Start with no user
    const { rerender } = render(<Login />);

    const emailInput = screen.getByPlaceholderText("Email address");
    const passwordInput = screen.getByPlaceholderText("Password");
    const submitButton = screen.getByRole("button", { name: /sign in/i });

    // Mock successful login that returns the user
    mockLogin.mockResolvedValueOnce(mockUser);

    // Submit the form
    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.click(submitButton);

    // Wait for login to be called
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled();
    });

    // Update the auth context with the logged-in user
    vi.mocked(useAuth).mockReturnValue({
      login: mockLogin,
      user: mockUser,
      token: "mock-token",
      isLoading: false,
      logout: vi.fn(),
    });

    // Rerender with the new auth context value
    rerender(<Login />);

    // Now the useEffect should trigger and navigate
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
    });
  });
});
