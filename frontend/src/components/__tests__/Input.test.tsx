import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Input from "../Input";

describe("Input Component", () => {
  it("renders correctly with default props", () => {
    render(<Input placeholder="Enter text" />);
    const input = screen.getByPlaceholderText("Enter text");
    expect(input).toBeInTheDocument();
    expect(input.tagName).toBe("INPUT");
  });

  it("displays label when provided", () => {
    render(<Input label="Username" placeholder="Enter username" />);
    expect(screen.getByText("Username")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter username")).toBeInTheDocument();
  });

  it("shows error message when error prop is provided", () => {
    const errorMessage = "This field is required";
    render(<Input error={errorMessage} placeholder="Enter text" />);
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    const input = screen.getByPlaceholderText("Enter text");
    expect(input).toHaveClass("border-red-500");
  });

  it("shows helper text when provided and no error", () => {
    const helperText = "Enter your full name";
    render(<Input helperText={helperText} placeholder="Enter text" />);
    expect(screen.getByText(helperText)).toBeInTheDocument();
  });

  it("prioritizes error message over helper text", () => {
    const helperText = "Enter your full name";
    const errorMessage = "This field is required";
    render(
      <Input
        helperText={helperText}
        error={errorMessage}
        placeholder="Enter text"
      />
    );
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(screen.queryByText(helperText)).not.toBeInTheDocument();
  });

  it("renders left icon when provided", () => {
    const leftIcon = <span data-testid="left-icon">🔍</span>;
    render(<Input leftIcon={leftIcon} placeholder="Search" />);
    expect(screen.getByTestId("left-icon")).toBeInTheDocument();
    const input = screen.getByPlaceholderText("Search");
    expect(input).toHaveClass("pl-10");
  });

  it("renders right icon when provided", () => {
    const rightIcon = <span data-testid="right-icon">✓</span>;
    render(<Input rightIcon={rightIcon} placeholder="Enter text" />);
    expect(screen.getByTestId("right-icon")).toBeInTheDocument();
    const input = screen.getByPlaceholderText("Enter text");
    expect(input).toHaveClass("pr-10");
  });

  it("passes additional props to the input element", async () => {
    const handleChange = vi.fn();
    render(
      <Input
        placeholder="Enter text"
        onChange={handleChange}
        maxLength={10}
        required
      />
    );

    const input = screen.getByPlaceholderText("Enter text");
    expect(input).toHaveAttribute("maxLength", "10");
    expect(input).toHaveAttribute("required");

    await userEvent.type(input, "test");
    expect(handleChange).toHaveBeenCalledTimes(4);
  });

  it("applies custom className when provided", () => {
    render(<Input placeholder="Enter text" className="custom-class" />);
    const input = screen.getByPlaceholderText("Enter text");
    expect(input).toHaveClass("custom-class");
  });

  it("forwards ref to the input element", () => {
    const ref = React.createRef<HTMLInputElement>();
    render(<Input ref={ref} placeholder="Enter text" />);
    expect(ref.current).not.toBeNull();
    expect(ref.current?.tagName).toBe("INPUT");
  });
});
