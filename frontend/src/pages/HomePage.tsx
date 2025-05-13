import React, { useState } from "react";
import Layout from "../components/Layout";
import FileUpload from "../components/FileUpload";
import TextArea from "../components/TextArea";
import Input from "../components/Input";
import Button from "../components/Button";
import { useGenerateQuiz, useUploadDocument } from "../hooks/useQuiz";

interface TabProps {
  label: string;
  active: boolean;
  onClick: () => void;
}

const Tab: React.FC<TabProps> = ({ label, active, onClick }) => (
  <button
    className={`py-3 px-6 text-center transition-all duration-200 ${
      active
        ? "border-b-2 border-indigo-500 text-indigo-600 dark:text-indigo-400 font-medium"
        : "text-gray-600 dark:text-gray-400 hover:text-indigo-500 dark:hover:text-indigo-300"
    }`}
    onClick={onClick}
  >
    {label}
  </button>
);

type TabType = "upload" | "text";

const HomePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [content, setContent] = useState("");
  const [topic, setTopic] = useState("");
  const [numQuestions, setNumQuestions] = useState(5);
  const [error, setError] = useState<string | null>(null);

  const generateQuizMutation = useGenerateQuiz();
  const uploadDocumentMutation = useUploadDocument();

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    setError(null);
  };

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file to upload");
      return;
    }

    try {
      const result = await uploadDocumentMutation.mutateAsync({
        file,
        topic: topic || undefined,
        num_questions: numQuestions,
      });

      // Navigate to quiz page
      window.location.href = `/quiz/${result.id}`;
    } catch (error) {
      console.error("Error uploading document:", error);
      setError(
        "An error occurred while processing your document. Please try again."
      );
    }
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content) {
      setError("Please enter some text content");
      return;
    }

    try {
      const result = await generateQuizMutation.mutateAsync({
        content,
        topic: topic || undefined,
        num_questions: numQuestions,
      });

      // Navigate to quiz page
      window.location.href = `/quiz/${result.id}`;
    } catch (error) {
      console.error("Error generating quiz:", error);
      setError(
        "An error occurred while generating your quiz. Please try again."
      );
    }
  };

  const isLoading =
    uploadDocumentMutation.isPending || generateQuizMutation.isPending;

  return (
    <Layout>
      {/* Hero Section */}
      <div className="mb-12 text-center animate-fade-in">
        <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400 text-transparent bg-clip-text">
          Transform Your Content Into Quizzes
        </h1>
        <p className="text-lg md:text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto mb-6">
          Upload documents or paste text to generate AI-powered quizzes
          instantly. Perfect for learning, testing knowledge, or creating
          educational content.
        </p>
        <div className="flex justify-center space-x-4 mb-8">
          <div className="flex items-center text-gray-600 dark:text-gray-300">
            <svg
              className="w-5 h-5 mr-2 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span>PDF Documents</span>
          </div>
          <div className="flex items-center text-gray-600 dark:text-gray-300">
            <svg
              className="w-5 h-5 mr-2 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span>Plain Text</span>
          </div>
          <div className="flex items-center text-gray-600 dark:text-gray-300">
            <svg
              className="w-5 h-5 mr-2 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span>Any Topic</span>
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto animate-slide-up">
        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border-l-4 border-red-500 text-red-700 dark:text-red-400 rounded shadow-sm">
            <div className="flex">
              <svg
                className="h-5 w-5 mr-3 text-red-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <span>{error}</span>
            </div>
          </div>
        )}

        <div className="bg-white dark:bg-gray-800 shadow-soft rounded-xl overflow-hidden transition-all duration-300">
          <div className="flex border-b border-gray-200 dark:border-gray-700">
            <Tab
              label="Upload Document"
              active={activeTab === "upload"}
              onClick={() => handleTabChange("upload")}
            />
            <Tab
              label="Enter Text"
              active={activeTab === "text"}
              onClick={() => handleTabChange("text")}
            />
          </div>

          <div className="p-6 md:p-8">
            <div
              className={`transition-opacity duration-300 ${
                activeTab === "upload"
                  ? "opacity-100"
                  : "opacity-0 h-0 absolute"
              }`}
            >
              <form
                onSubmit={handleUploadSubmit}
                className={activeTab === "upload" ? "" : "hidden"}
              >
                <div className="mb-6">
                  <FileUpload
                    label="Upload a document"
                    onFileSelect={handleFileSelect}
                    accept=".pdf,.txt,.doc,.docx"
                  />
                </div>

                <div className="space-y-5">
                  <Input
                    label="Topic (optional)"
                    placeholder="e.g., Science, History, Programming"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                  />

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Number of Questions: {numQuestions}
                    </label>
                    <input
                      type="range"
                      min="3"
                      max="10"
                      value={numQuestions}
                      onChange={(e) =>
                        setNumQuestions(parseInt(e.target.value))
                      }
                      className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-md appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mt-1">
                      <span>3</span>
                      <span>10</span>
                    </div>
                  </div>

                  <div className="pt-4">
                    <Button
                      type="submit"
                      disabled={!file || isLoading}
                      isLoading={uploadDocumentMutation.isPending}
                      className="w-full transition-all duration-300 hover:shadow-md"
                    >
                      Generate Quiz
                    </Button>
                  </div>
                </div>
              </form>
            </div>

            <div
              className={`transition-opacity duration-300 ${
                activeTab === "text" ? "opacity-100" : "opacity-0 h-0 absolute"
              }`}
            >
              <form
                onSubmit={handleTextSubmit}
                className={activeTab === "text" ? "" : "hidden"}
              >
                <div className="mb-6">
                  <TextArea
                    label="Enter text content"
                    placeholder="Paste or type the content you want to create a quiz for..."
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    rows={8}
                    required
                    className="dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>

                <div className="space-y-5">
                  <Input
                    label="Topic (optional)"
                    placeholder="e.g., Science, History, Programming"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Number of Questions: {numQuestions}
                    </label>
                    <input
                      type="range"
                      min="3"
                      max="10"
                      value={numQuestions}
                      onChange={(e) =>
                        setNumQuestions(parseInt(e.target.value))
                      }
                      className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-md appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mt-1">
                      <span>3</span>
                      <span>10</span>
                    </div>
                  </div>

                  <div className="pt-4">
                    <Button
                      type="submit"
                      disabled={!content || isLoading}
                      isLoading={generateQuizMutation.isPending}
                      className="w-full transition-all duration-300 hover:shadow-md"
                    >
                      Generate Quiz
                    </Button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>

        {/* Features section */}
        <div className="mt-16 grid md:grid-cols-3 gap-6 animate-fade-in">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-soft transition-all duration-300 hover:shadow-md">
            <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-indigo-600 dark:text-indigo-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
              Fast Generation
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Generate quizzes in seconds using our advanced AI algorithms.
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-soft transition-all duration-300 hover:shadow-md">
            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-purple-600 dark:text-purple-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
              Smart Questions
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Context-aware questions that test knowledge comprehension.
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-soft transition-all duration-300 hover:shadow-md">
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-green-600 dark:text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
              Instant Results
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Get immediate feedback with detailed explanations for each answer.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default HomePage;
