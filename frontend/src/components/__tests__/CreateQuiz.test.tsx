// Mock the hooks
const mockMutateAsync = vi.fn().mockResolvedValue({ id: "123" });

vi.mock("../../hooks/useQuiz", () => ({
  useGenerateQuiz: () => ({
    mutateAsync: mockMutateAsync,
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    isSuccess: true,
    isIdle: false,
    status: "success",
    data: null,
    error: null,
    reset: vi.fn(),
    failureCount: 0,
    failureReason: null,
    variables: undefined,
  }),
  useUploadDocument: () => ({
    mutateAsync: vi.fn().mockResolvedValue({ id: "123" }),
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    isSuccess: true,
    isIdle: false,
    status: "success",
    data: null,
    error: null,
    reset: vi.fn(),
    failureCount: 0,
    failureReason: null,
    variables: undefined,
  }),
}));

import { render, screen, act, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import CreateQuiz from "../CreateQuiz";

// Create a wrapper with necessary providers
const queryClient = new QueryClient();
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

describe("CreateQuiz", () => {
  it("renders both upload and text input tabs", () => {
    render(<CreateQuiz />, { wrapper });

    expect(screen.getByText("Upload Document")).toBeInTheDocument();
    expect(screen.getByText("Enter Text")).toBeInTheDocument();
  });

  it("switches between upload and text input modes", async () => {
    const user = userEvent.setup();
    render(<CreateQuiz />, { wrapper });

    // Should start with upload mode
    expect(screen.getByText("Upload Document")).toHaveClass("bg-indigo-100");

    // Switch to text mode
    await act(async () => {
      await user.click(screen.getByText("Enter Text"));
    });
    expect(screen.getByText("Enter Text")).toHaveClass("bg-indigo-100");
  });

  it("shows validation error when trying to submit without file", async () => {
    render(<CreateQuiz />, { wrapper });

    // Find the form and submit button
    const form = screen.getByRole("form");
    await act(async () => {
      // Submit the form directly since the button is disabled
      form.dispatchEvent(new Event("submit", { bubbles: true }));
    });

    // Wait for the error message
    const errorMessage = await screen.findByText(
      "Please select a file to upload"
    );
    expect(errorMessage).toBeInTheDocument();
  });

  it("shows validation error when trying to submit without text", async () => {
    const user = userEvent.setup();
    render(<CreateQuiz />, { wrapper });

    await act(async () => {
      // Switch to text mode
      await user.click(screen.getByText("Enter Text"));
    });

    // Find the form and submit button
    const form = screen.getByRole("form");
    await act(async () => {
      // Submit the form directly since the button is disabled
      form.dispatchEvent(new Event("submit", { bubbles: true }));
    });

    // Wait for the error message
    const errorMessage = await screen.findByText(
      "Please enter some text content"
    );
    expect(errorMessage).toBeInTheDocument();
  });

  it("allows setting topic and number of questions", async () => {
    const user = userEvent.setup();
    render(<CreateQuiz />, { wrapper });

    const topicInput = screen.getByPlaceholderText(
      "Enter a topic for your quiz"
    );
    const numQuestionsInput = screen.getByLabelText("Number of Questions");

    await act(async () => {
      await user.type(topicInput, "History");
      await user.clear(numQuestionsInput);
      await user.type(numQuestionsInput, "10");
    });

    expect(topicInput).toHaveValue("History");
    expect(numQuestionsInput).toHaveValue(10);
  });

  it("handles file upload", async () => {
    const user = userEvent.setup();
    render(<CreateQuiz />, { wrapper });

    const file = new File(["test content"], "test.txt", { type: "text/plain" });
    const fileInput = screen.getByLabelText(/upload file/i) as HTMLInputElement;

    await act(async () => {
      await user.upload(fileInput, file);
    });

    expect(fileInput.files?.[0]).toBe(file);
    expect(fileInput.files?.length).toBe(1);
  });

  it("handles text input submission", async () => {
    render(<CreateQuiz />, { wrapper });

    // Click the "Enter Text" tab
    fireEvent.click(screen.getByText(/enter text/i));

    // Find and fill in the text area
    const textArea = screen.getByLabelText(/enter your text/i);
    fireEvent.change(textArea, { target: { value: "Sample text content" } });

    // Fill in topic and number of questions
    const topicInput = screen.getByLabelText(/topic/i);
    fireEvent.change(topicInput, { target: { value: "Sample Topic" } });

    const questionsInput = screen.getByLabelText(/number of questions/i);
    fireEvent.change(questionsInput, { target: { value: "5" } });

    // Submit the form
    const submitButton = screen.getByRole("button", { name: /create quiz/i });
    fireEvent.click(submitButton);

    // Verify that mutateAsync was called with the correct data
    expect(mockMutateAsync).toHaveBeenCalledWith({
      content: "Sample text content",
      topic: "Sample Topic",
      num_questions: 5,
    });
  });
});
