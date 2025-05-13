import React from "react";

// Define button variants
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
  // Base button styles
  const baseStyles = `
    inline-flex items-center justify-center font-medium transition-all duration-200
    focus:outline-none focus:ring-2 focus:ring-offset-2 
    rounded-lg transform hover:-translate-y-0.5 active:translate-y-0
  `;

  // Size styles
  const sizeStyles = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2.5",
    lg: "px-6 py-3 text-lg",
  };

  // Variant-specific styles
  const variantStyles = {
    primary: `bg-gradient-to-r from-indigo-600 to-purple-600 text-white 
              hover:from-indigo-700 hover:to-purple-700 
              dark:from-indigo-500 dark:to-purple-500 
              dark:hover:from-indigo-600 dark:hover:to-purple-600 
              focus:ring-indigo-500`,
    secondary: `bg-gray-200 text-gray-800 hover:bg-gray-300 
                dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600 
                focus:ring-gray-500`,
    outline: `border border-gray-300 text-gray-700 hover:bg-gray-50 
              dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800 
              focus:ring-indigo-500`,
    danger: `bg-gradient-to-r from-red-500 to-pink-500 text-white 
             hover:from-red-600 hover:to-pink-600 
             dark:from-red-600 dark:to-pink-600 
             dark:hover:from-red-700 dark:hover:to-pink-700 
             focus:ring-red-500`,
    success: `bg-gradient-to-r from-green-500 to-teal-500 text-white 
              hover:from-green-600 hover:to-teal-600 
              dark:from-green-600 dark:to-teal-600 
              dark:hover:from-green-700 dark:hover:to-teal-700 
              focus:ring-green-500`,
  };

  // Loading and disabled styles
  const loadingStyles = isLoading ? "opacity-80 cursor-wait" : "";
  const disabledStyles = disabled
    ? "opacity-60 cursor-not-allowed transform-none hover:translate-y-0"
    : "";
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
