import type { ChangeEvent } from "react";
import { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Input from "../components/Input";
import Button from "../components/Button";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { login, user } = useAuth();
  const successMessage =
    (location.state as { message?: string } | null)?.message ?? "";

  useEffect(() => {
    if (user) {
      navigate("/dashboard");
    }
  }, [user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await login({ email, password });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to login");
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    if (name === "email") setEmail(value);
    if (name === "password") setPassword(value);
  };

  return (
    <div className="mx-auto w-full max-w-md">
      <div className="card p-6 sm:p-8">
        <p className="page-kicker mb-2">Welcome back</p>
        <h2 className="font-display text-3xl font-semibold text-stone-900 dark:text-white">
          Sign in to your account
        </h2>
        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          {successMessage && (
            <div className="rounded-xl bg-teal-50 dark:bg-teal-950/40 p-4">
              <div className="text-sm text-teal-800 dark:text-teal-300">
                {successMessage}
              </div>
            </div>
          )}
          {error && (
            <div className="rounded-xl bg-red-50 dark:bg-red-900/30 p-4">
              <div className="text-sm text-red-700 dark:text-red-400">
                {error}
              </div>
            </div>
          )}
          <Input
            type="email"
            name="email"
            label="Email"
            autoComplete="email"
            required
            value={email}
            onChange={handleInputChange}
            placeholder="Email address"
          />
          <Input
            type="password"
            name="password"
            label="Password"
            autoComplete="current-password"
            required
            value={password}
            onChange={handleInputChange}
            placeholder="Password"
          />

          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading ? "Signing in..." : "Sign in"}
          </Button>
        </form>
        <p className="mt-6 text-center text-sm text-stone-600 dark:text-stone-400">
          New here?{" "}
          <Link
            to="/register"
            className="font-semibold text-teal-800 hover:text-teal-900 dark:text-teal-300"
          >
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
