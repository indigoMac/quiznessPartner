import React from "react";
import "../test.css";

const TestComponent: React.FC = () => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold text-indigo-700 mb-4">
        Testing Tailwind CSS
      </h1>

      {/* Basic Tailwind classes */}
      <div className="flex flex-col space-y-4">
        <div className="bg-blue-500 text-white p-4 rounded-md">
          This is a blue box with white text
        </div>
        <div className="bg-green-500 text-white p-4 rounded-md">
          This is a green box with white text
        </div>
        <div className="bg-red-500 text-white p-4 rounded-md">
          This is a red box with white text
        </div>
      </div>

      {/* Using the @apply class from test.css */}
      <div className="mt-8">
        <div className="test-container">
          This element uses @apply directive from test.css
        </div>
      </div>

      {/* Testing dark mode */}
      <div className="mt-8 p-4 bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-md">
        This element should change in dark mode
      </div>

      {/* Testing gradient */}
      <div className="mt-8 h-20 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-md"></div>
    </div>
  );
};

export default TestComponent;
