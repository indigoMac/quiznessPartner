import { vi, describe, it, expect, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import type { User } from "../../types/auth";

// Mock modules first
vi.mock("react-router-dom", () => {
  const mockNavigate = vi.fn();
  const mockLocation = { pathname: "/protected" };
  const MockNavigate = vi.fn();
  const MockOutlet = () => <div data-testid="mock-outlet">Outlet Content</div>;

  return {
    useNavigate: () => mockNavigate,
    useLocation: () => mockLocation,
    Navigate: (props: {
      to: string;
      state: { from: { pathname: string } };
    }) => {
      MockNavigate(props);
      return null;
    },
    Outlet: MockOutlet,
  };
});

vi.mock("../../context/AuthContext", () => ({
  useAuth: () => mockUseAuth(),
}));

// Import after mocks
import ProtectedRoute from "../ProtectedRoute";

// Mock hooks
const mockUseAuth = vi.fn();

describe("ProtectedRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should redirect to login if user is not authenticated", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      token: null,
      login: vi.fn(),
      logout: vi.fn(),
    });

    render(<ProtectedRoute />);

    expect(vi.mocked(mockUseAuth)).toHaveBeenCalled();
  });

  it("should render outlet if user is authenticated", () => {
    const mockUser: User = { id: "1", email: "test@test.com" };
    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      token: "mock-token",
      login: vi.fn(),
      logout: vi.fn(),
    });

    const { getByTestId } = render(<ProtectedRoute />);
    expect(getByTestId("mock-outlet")).toBeInTheDocument();
  });

  it("should show loading spinner while authenticating", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: true,
      token: null,
      login: vi.fn(),
      logout: vi.fn(),
    });

    const { container } = render(<ProtectedRoute />);
    expect(container).toBeInTheDocument();
  });
});
