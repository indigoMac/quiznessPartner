import { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import { login as loginApi, getCurrentUser } from "../api/auth";
import type { User, LoginCredentials, AuthContextType } from "../types/auth";

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem("token")
  );
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (token) {
      getCurrentUser(token)
        .then((userData) => {
          setUser(userData);
          setIsLoading(false);
        })
        .catch(() => {
          setToken(null);
          localStorage.removeItem("token");
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const login = async (credentials: LoginCredentials) => {
    const { access_token } = await loginApi(credentials);
    setToken(access_token);
    localStorage.setItem("token", access_token);

    // Wait for user data before completing login
    const userData = await getCurrentUser(access_token);
    setUser(userData);
    return userData; // Return the user data for the login page to use
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("token");
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
