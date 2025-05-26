import { useState } from "react";
import type { ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import FileUpload from "./FileUpload";
import TextArea from "./TextArea";
import Input from "./Input";
import Button from "./Button";
import { useGenerateQuiz, useUploadDocument } from "../hooks/useQuiz";
import type { AxiosError } from "axios";

type TabType = "upload" | "text";

interface TabProps {
  label: string;
  active: boolean;
  onClick: () => void;
}

const Tab: React.FC<TabProps> = ({ label, active, onClick }) => (
  <button
    className={`px-4 py-2 font-medium rounded-lg transition-colors duration-200
      ${
        active
          ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300"
          : "text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
      }
    `}
    onClick={onClick}
  >
    {label}
  </button>
);

export default function CreateQuiz() {
  const [activeTab, setActiveTab] = useState<TabType>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [content, setContent] = useState("");
  const [topic, setTopic] = useState("");
  const [numQuestions, setNumQuestions] = useState(5);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

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

      navigate(`/quiz/${result.id}`);
    } catch (error: unknown) {
      console.error("Error uploading document:", error);
      setError(
        ((error as AxiosError)?.response?.data as { detail: string })?.detail ||
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

      navigate(`/quiz/${result.id}`);
    } catch (error: unknown) {
      console.error("Error generating quiz:", error);
      setError(
        ((error as AxiosError)?.response?.data as { detail: string })?.detail ||
          "An error occurred while generating your quiz. Please try again."
      );
    }
  };

  const isLoading =
    uploadDocumentMutation.isPending || generateQuizMutation.isPending;

  return (
    <div className="max-w-3xl mx-auto animate-slide-up">
      <h1 className="text-3xl font-bold mb-8">Create New Quiz</h1>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="mb-6">
          <div className="flex space-x-4 mb-6">
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

          <form
            role="form"
            onSubmit={
              activeTab === "upload" ? handleUploadSubmit : handleTextSubmit
            }
          >
            <div className="space-y-6">
              <div>
                <Input
                  label="Topic (Optional)"
                  value={topic}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setTopic(e.target.value)
                  }
                  placeholder="Enter a topic for your quiz"
                />
              </div>

              <div>
                <Input
                  type="number"
                  label="Number of Questions"
                  value={numQuestions}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setNumQuestions(parseInt(e.target.value, 10))
                  }
                  min={1}
                  max={20}
                />
              </div>

              {activeTab === "upload" ? (
                <div>
                  <FileUpload
                    onFileSelect={handleFileSelect}
                    accept=".txt,.pdf,.doc,.docx"
                  />
                </div>
              ) : (
                <div>
                  <TextArea
                    label="Enter your text"
                    value={content}
                    onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                      setContent(e.target.value)
                    }
                    placeholder="Enter the text you want to generate questions from..."
                    rows={10}
                    required
                  />
                </div>
              )}

              <div>
                <Button
                  type="submit"
                  disabled={
                    isLoading ||
                    (activeTab === "text" && !content) ||
                    (activeTab === "upload" && !file)
                  }
                  isLoading={isLoading}
                  className="w-full"
                >
                  {isLoading ? "Creating Quiz..." : "Create Quiz"}
                </Button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
