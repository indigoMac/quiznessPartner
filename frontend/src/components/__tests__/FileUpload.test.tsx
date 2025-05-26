// import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import FileUpload from "../FileUpload";

describe("FileUpload Component", () => {
  const onFileSelect = vi.fn();

  beforeEach(() => {
    onFileSelect.mockClear();
  });

  it("renders with default props", () => {
    render(<FileUpload onFileSelect={onFileSelect} />);
    expect(screen.getByText("Upload file")).toBeInTheDocument();
    expect(screen.getByText(/Drag and drop a file here/)).toBeInTheDocument();
    expect(screen.getByText(/Max file size: 10MB/)).toBeInTheDocument();
  });

  it("renders with custom label", () => {
    render(<FileUpload onFileSelect={onFileSelect} label="Custom Label" />);
    expect(screen.getByText("Custom Label")).toBeInTheDocument();
  });

  it("shows custom max file size", () => {
    render(<FileUpload onFileSelect={onFileSelect} maxSize={5} />);
    expect(screen.getByText(/Max file size: 5MB/)).toBeInTheDocument();
  });

  it("shows custom accepted formats", () => {
    render(<FileUpload onFileSelect={onFileSelect} accept=".jpg,.png" />);
    expect(screen.getByText(/Accepted formats: .jpg,.png/)).toBeInTheDocument();
  });

  it("shows error message when provided", () => {
    const errorMessage = "This is an error";
    render(<FileUpload onFileSelect={onFileSelect} error={errorMessage} />);
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it("handles file selection via button click", () => {
    render(<FileUpload onFileSelect={onFileSelect} />);

    const file = new File(["test content"], "test.txt", { type: "text/plain" });
    const input = screen.getByRole("button", { name: "Select file" });

    // Mock file input change
    const fileInput = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;
    Object.defineProperty(fileInput, "files", {
      value: [file],
    });

    fireEvent.click(input);
    fireEvent.change(fileInput);

    expect(onFileSelect).toHaveBeenCalledWith(file);
  });

  it("shows selected file name after selection", () => {
    render(<FileUpload onFileSelect={onFileSelect} />);

    const file = new File(["test content"], "test.txt", { type: "text/plain" });
    const fileInput = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;

    Object.defineProperty(fileInput, "files", {
      value: [file],
    });

    fireEvent.change(fileInput);

    expect(screen.getByText("Selected: test.txt")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Change file" })
    ).toBeInTheDocument();
  });

  it("validates file size", () => {
    render(<FileUpload onFileSelect={onFileSelect} maxSize={0.00001} />);

    // Create a file larger than the max size (0.00001MB = ~10 bytes)
    const largeContent = "x".repeat(1000);
    const file = new File([largeContent], "large.txt", { type: "text/plain" });
    const fileInput = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;

    Object.defineProperty(fileInput, "files", {
      value: [file],
    });

    fireEvent.change(fileInput);

    expect(screen.getByText(/File is too large/)).toBeInTheDocument();
    expect(onFileSelect).not.toHaveBeenCalled();
  });

  it("validates file type", () => {
    render(<FileUpload onFileSelect={onFileSelect} accept=".jpg,.png" />);

    const file = new File(["test content"], "test.txt", { type: "text/plain" });
    const fileInput = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;

    Object.defineProperty(fileInput, "files", {
      value: [file],
    });

    fireEvent.change(fileInput);

    expect(screen.getByText(/File type not supported/)).toBeInTheDocument();
    expect(onFileSelect).not.toHaveBeenCalled();
  });

  it("handles drag events", () => {
    const { container } = render(<FileUpload onFileSelect={onFileSelect} />);
    const dropzone = container.firstChild?.lastChild as HTMLElement;

    // Test dragenter
    fireEvent.dragEnter(dropzone);
    expect(dropzone).toHaveClass("border-blue-500");

    // Test dragleave
    fireEvent.dragLeave(dropzone);
    expect(dropzone).not.toHaveClass("border-blue-500");
  });

  it("handles file drop", () => {
    const { container } = render(<FileUpload onFileSelect={onFileSelect} />);
    const dropzone = container.firstChild?.lastChild as HTMLElement;

    const file = new File(["test content"], "test.txt", { type: "text/plain" });

    // Mock dataTransfer
    const dataTransfer = {
      files: [file],
    };

    fireEvent.drop(dropzone, { dataTransfer });

    expect(onFileSelect).toHaveBeenCalledWith(file);
    expect(screen.getByText("Selected: test.txt")).toBeInTheDocument();
  });
});
