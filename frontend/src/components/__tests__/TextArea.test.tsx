import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TextArea from "../TextArea";

describe("TextArea Component", () => {
  it("renders correctly with default props", () => {
    render(<TextArea placeholder="Enter text" />);
    const textarea = screen.getByPlaceholderText("Enter text");
    expect(textarea).toBeInTheDocument();
    expect(textarea.tagName).toBe("TEXTAREA");
  });

  it("displays label when provided", () => {
    render(<TextArea label="Description" placeholder="Enter description" />);
    expect(screen.getByText("Description")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Enter description")
    ).toBeInTheDocument();
  });

  it("shows error message when error prop is provided", () => {
    const errorMessage = "This field is required";
    render(<TextArea error={errorMessage} placeholder="Enter text" />);
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    const textarea = screen.getByPlaceholderText("Enter text");
    expect(textarea).toHaveClass("border-red-500");
  });

  it("shows helper text when provided and no error", () => {
    const helperText = "Enter your detailed description";
    render(<TextArea helperText={helperText} placeholder="Enter text" />);
    expect(screen.getByText(helperText)).toBeInTheDocument();
  });

  it("prioritizes error message over helper text", () => {
    const helperText = "Enter your detailed description";
    const errorMessage = "This field is required";
    render(
      <TextArea
        helperText={helperText}
        error={errorMessage}
        placeholder="Enter text"
      />
    );
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(screen.queryByText(helperText)).not.toBeInTheDocument();
  });

  it("passes additional props to the textarea element", async () => {
    const handleChange = vi.fn();
    render(
      <TextArea
        placeholder="Enter text"
        onChange={handleChange}
        maxLength={100}
        required
      />
    );

    const textarea = screen.getByPlaceholderText("Enter text");
    expect(textarea).toHaveAttribute("maxLength", "100");
    expect(textarea).toHaveAttribute("required");

    await userEvent.type(textarea, "test");
    expect(handleChange).toHaveBeenCalledTimes(4);
  });

  it("applies custom className when provided", () => {
    render(<TextArea placeholder="Enter text" className="custom-class" />);
    const textarea = screen.getByPlaceholderText("Enter text");
    expect(textarea).toHaveClass("custom-class");
  });

  it("forwards ref to the textarea element", () => {
    const ref = React.createRef<HTMLTextAreaElement>();
    render(<TextArea ref={ref} placeholder="Enter text" />);
    expect(ref.current).not.toBeNull();
    expect(ref.current?.tagName).toBe("TEXTAREA");
  });

  it("has resize-none class by default", () => {
    render(<TextArea placeholder="Enter text" />);
    const textarea = screen.getByPlaceholderText("Enter text");
    expect(textarea).toHaveClass("resize-none");
  });

  it("has default rows set to 5", () => {
    render(<TextArea placeholder="Enter text" />);
    const textarea = screen.getByPlaceholderText("Enter text");
    expect(textarea).toHaveAttribute("rows", "5");
  });

  it("allows overriding the default rows", () => {
    render(<TextArea placeholder="Enter text" rows={10} />);
    const textarea = screen.getByPlaceholderText("Enter text");
    expect(textarea).toHaveAttribute("rows", "10");
  });
});
