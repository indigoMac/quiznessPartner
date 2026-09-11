import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Bars3Icon, MoonIcon, SunIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { useAuth } from "../context/AuthContext";

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();

  useEffect(() => {
    if (
      localStorage.theme === "dark" ||
      (!("theme" in localStorage) &&
        window.matchMedia("(prefers-color-scheme: dark)").matches)
    ) {
      setIsDarkMode(true);
      document.documentElement.classList.add("dark");
    } else {
      setIsDarkMode(false);
      document.documentElement.classList.remove("dark");
    }
  }, []);

  useEffect(() => {
    setIsMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    document.body.style.overflow = isMenuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [isMenuOpen]);

  const toggleDarkMode = () => {
    if (isDarkMode) {
      localStorage.theme = "light";
      document.documentElement.classList.remove("dark");
    } else {
      localStorage.theme = "dark";
      document.documentElement.classList.add("dark");
    }
    setIsDarkMode(!isDarkMode);
  };

  const navLinkClass = (path: string) =>
    `min-h-11 inline-flex items-center px-1 text-sm font-medium transition-colors ${
      location.pathname === path
        ? "text-teal-800 dark:text-teal-300"
        : "text-stone-600 hover:text-stone-900 dark:text-stone-300 dark:hover:text-white"
    }`;

  const mobileLinkClass = (path: string) =>
    `flex min-h-12 items-center rounded-xl px-4 text-base font-medium ${
      location.pathname === path
        ? "bg-teal-50 text-teal-900 dark:bg-teal-950/60 dark:text-teal-200"
        : "text-stone-800 dark:text-stone-100"
    }`;

  return (
    <div className="min-h-[100dvh] flex flex-col bg-paper text-ink dark:bg-paper-dark dark:text-stone-100">
      <header className="sticky top-0 z-40 border-b border-stone-200/80 bg-paper/90 pt-[env(safe-area-inset-top)] backdrop-blur-md dark:border-stone-800 dark:bg-paper-dark/90">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
          <Link to="/" className="flex min-h-11 items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-800 text-white">
              <svg
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <path
                  d="M4 9h16v10a2 2 0 01-2 2H6a2 2 0 01-2-2V9zm2-5h12a2 2 0 012 2v2H4V6a2 2 0 012-2z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <span className="font-display text-lg font-semibold tracking-tight">
              Quizness Partner
            </span>
          </Link>

          <div className="flex items-center gap-1 sm:gap-2">
            <nav className="hidden md:block" aria-label="Main">
              <ul className="flex items-center gap-5">
                <li>
                  <Link to="/" className={navLinkClass("/")}>
                    Home
                  </Link>
                </li>
                {user ? (
                  <>
                    <li>
                      <Link
                        to="/dashboard"
                        className={navLinkClass("/dashboard")}
                      >
                        Dashboard
                      </Link>
                    </li>
                    <li>
                      <Link to="/quiz/new" className={navLinkClass("/quiz/new")}>
                        Create
                      </Link>
                    </li>
                    <li>
                      <Link to="/profile" className={navLinkClass("/profile")}>
                        Profile
                      </Link>
                    </li>
                    <li>
                      <button
                        onClick={logout}
                        className="min-h-11 text-sm font-medium text-stone-600 hover:text-stone-900 dark:text-stone-300 dark:hover:text-white"
                      >
                        Logout
                      </button>
                    </li>
                  </>
                ) : (
                  <>
                    <li>
                      <Link to="/login" className={navLinkClass("/login")}>
                        Login
                      </Link>
                    </li>
                    <li>
                      <Link
                        to="/register"
                        className="inline-flex min-h-11 items-center rounded-xl bg-teal-800 px-4 text-sm font-semibold text-white hover:bg-teal-900"
                      >
                        Register
                      </Link>
                    </li>
                  </>
                )}
              </ul>
            </nav>

            <button
              onClick={toggleDarkMode}
              className="inline-flex h-11 w-11 items-center justify-center rounded-xl text-stone-700 hover:bg-stone-200/70 dark:text-stone-200 dark:hover:bg-stone-800"
              aria-label={
                isDarkMode ? "Switch to light mode" : "Switch to dark mode"
              }
            >
              {isDarkMode ? (
                <SunIcon className="h-5 w-5" />
              ) : (
                <MoonIcon className="h-5 w-5" />
              )}
            </button>

            <button
              type="button"
              className="inline-flex h-11 w-11 items-center justify-center rounded-xl text-stone-800 hover:bg-stone-200/70 md:hidden dark:text-stone-100 dark:hover:bg-stone-800"
              aria-expanded={isMenuOpen}
              aria-controls="mobile-navigation"
              aria-label={isMenuOpen ? "Close menu" : "Open menu"}
              onClick={() => setIsMenuOpen((open) => !open)}
            >
              {isMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {isMenuOpen && (
          <nav
            id="mobile-navigation"
            className="border-t border-stone-200 bg-paper px-4 py-3 pb-[max(1rem,env(safe-area-inset-bottom))] md:hidden dark:border-stone-800 dark:bg-paper-dark"
            aria-label="Mobile"
          >
            <ul className="flex flex-col gap-1">
              <li>
                <Link to="/" className={mobileLinkClass("/")}>
                  Home
                </Link>
              </li>
              {user ? (
                <>
                  <li>
                    <Link
                      to="/dashboard"
                      className={mobileLinkClass("/dashboard")}
                    >
                      Dashboard
                    </Link>
                  </li>
                  <li>
                    <Link
                      to="/quiz/new"
                      className={mobileLinkClass("/quiz/new")}
                    >
                      Create quiz
                    </Link>
                  </li>
                  <li>
                    <Link to="/profile" className={mobileLinkClass("/profile")}>
                      Profile
                    </Link>
                  </li>
                  <li>
                    <button
                      onClick={logout}
                      className="flex min-h-12 w-full items-center rounded-xl px-4 text-left text-base font-medium text-stone-800 dark:text-stone-100"
                    >
                      Logout
                    </button>
                  </li>
                </>
              ) : (
                <>
                  <li>
                    <Link to="/login" className={mobileLinkClass("/login")}>
                      Login
                    </Link>
                  </li>
                  <li>
                    <Link
                      to="/register"
                      className="mt-2 flex min-h-12 items-center justify-center rounded-xl bg-teal-800 px-4 text-base font-semibold text-white"
                    >
                      Register
                    </Link>
                  </li>
                </>
              )}
            </ul>
          </nav>
        )}
      </header>

      <main className="mx-auto w-full max-w-5xl flex-grow px-4 py-6 sm:py-10">
        {children}
      </main>

      <footer className="border-t border-stone-200 bg-white/70 py-6 pb-[max(1.5rem,env(safe-area-inset-bottom))] dark:border-stone-800 dark:bg-stone-950/40">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-3 px-4 text-sm text-stone-500 dark:text-stone-400 sm:flex-row">
          <p>© {new Date().getFullYear()} Quizness Partner</p>
          <p>Study from notes, PDFs, and links.</p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
