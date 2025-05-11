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
    className={`py-2 px-4 text-center ${
      active
        ? "border-b-2 border-blue-500 text-blue-600 font-medium"
        : "text-gray-500 hover:text-gray-700"
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

  const generateQuizMutation = useGenerateQuiz();
  const uploadDocumentMutation = useUploadDocument();

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
  };

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

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
    }
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content) return;

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
    }
  };

  const isLoading =
    uploadDocumentMutation.isPending || generateQuizMutation.isPending;

  return (
    <Layout>
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">
          Create an AI-Powered Quiz
        </h1>

        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          <div className="flex border-b">
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

          <div className="p-6">
            {activeTab === "upload" ? (
              <form onSubmit={handleUploadSubmit}>
                <div className="mb-6">
                  <FileUpload
                    label="Upload a document"
                    onFileSelect={handleFileSelect}
                    accept=".pdf,.txt,.doc,.docx"
                  />
                </div>

                <div className="space-y-4">
                  <Input
                    label="Topic (optional)"
                    placeholder="e.g., Science, History, Programming"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                  />

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Number of Questions
                    </label>
                    <input
                      type="range"
                      min="3"
                      max="10"
                      value={numQuestions}
                      onChange={(e) =>
                        setNumQuestions(parseInt(e.target.value))
                      }
                      className="w-full"
                    />
                    <div className="text-center text-sm text-gray-600">
                      {numQuestions} questions
                    </div>
                  </div>

                  <div className="pt-4">
                    <Button
                      type="submit"
                      disabled={!file || isLoading}
                      isLoading={uploadDocumentMutation.isPending}
                      className="w-full"
                    >
                      Generate Quiz
                    </Button>
                  </div>
                </div>
              </form>
            ) : (
              <form onSubmit={handleTextSubmit}>
                <div className="mb-6">
                  <TextArea
                    label="Enter text content"
                    placeholder="Paste or type the content you want to create a quiz for..."
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    rows={8}
                    required
                  />
                </div>

                <div className="space-y-4">
                  <Input
                    label="Topic (optional)"
                    placeholder="e.g., Science, History, Programming"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                  />

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Number of Questions
                    </label>
                    <input
                      type="range"
                      min="3"
                      max="10"
                      value={numQuestions}
                      onChange={(e) =>
                        setNumQuestions(parseInt(e.target.value))
                      }
                      className="w-full"
                    />
                    <div className="text-center text-sm text-gray-600">
                      {numQuestions} questions
                    </div>
                  </div>

                  <div className="pt-4">
                    <Button
                      type="submit"
                      disabled={!content || isLoading}
                      isLoading={generateQuizMutation.isPending}
                      className="w-full"
                    >
                      Generate Quiz
                    </Button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default HomePage;
