import React from "react";

type ButtonVariant = "primary" | "secondary" | "outline" | "danger" | "success";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  isLoading?: boolean;
  children: React.ReactNode;
  fullWidth?: boolean;
  size?: "sm" | "md" | "lg";
  icon?: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  isLoading = false,
  children,
  className = "",
  disabled,
  fullWidth = false,
  size = "md",
  icon,
  ...props
}) => {
  const baseStyles = `
    inline-flex items-center justify-center font-semibold
    focus:outline-none focus:ring-2 focus:ring-offset-2
    rounded-xl transition-colors duration-150
  `;

  const sizeStyles = {
    sm: "min-h-10 px-3 py-2 text-sm",
    md: "min-h-11 px-4 py-2.5 text-sm",
    lg: "min-h-12 px-6 py-3 text-base",
  };

  const variantStyles = {
    primary: `bg-teal-800 text-white hover:bg-teal-900
              dark:bg-teal-700 dark:hover:bg-teal-600
              focus:ring-teal-700`,
    secondary: `bg-stone-200 text-stone-800 hover:bg-stone-300
                dark:bg-stone-700 dark:text-stone-100 dark:hover:bg-stone-600
                focus:ring-stone-500`,
    outline: `border border-stone-300 text-stone-800 bg-white hover:bg-stone-50
              dark:border-stone-600 dark:text-stone-200 dark:bg-transparent dark:hover:bg-stone-800
              focus:ring-teal-700`,
    danger: `bg-red-700 text-white hover:bg-red-800
             dark:bg-red-700 dark:hover:bg-red-600
             focus:ring-red-600`,
    success: `bg-teal-700 text-white hover:bg-teal-800
              dark:bg-teal-600 dark:hover:bg-teal-500
              focus:ring-teal-700`,
  };

  const loadingStyles = isLoading ? "opacity-80 cursor-wait" : "";
  const disabledStyles = disabled ? "opacity-60 cursor-not-allowed" : "";
  const widthStyles = fullWidth ? "w-full" : "";

  return (
    <button
      className={`
        ${baseStyles}
        ${sizeStyles[size]}
        ${variantStyles[variant]}
        ${loadingStyles}
        ${disabledStyles}
        ${widthStyles}
        ${className}
      `}
      disabled={isLoading || disabled}
      {...props}
    >
      {isLoading ? (
        <div className="flex items-center justify-center">
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          {children}
        </div>
      ) : (
        <div className="flex items-center justify-center">
          {icon && <span className="mr-2">{icon}</span>}
          {children}
        </div>
      )}
    </button>
  );
};

export default Button;
