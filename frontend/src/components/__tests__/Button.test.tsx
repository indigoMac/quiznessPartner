import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Button from "../Button";

describe("Button Component", () => {
  it("renders children correctly", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("applies the correct variant classes", () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);
    const button = screen.getByRole("button");
    expect(button).toHaveClass("from-indigo-600");
    expect(button).toHaveClass("to-purple-600");

    rerender(<Button variant="secondary">Secondary</Button>);
    const secondaryButton = screen.getByRole("button");
    expect(secondaryButton).toHaveClass("bg-gray-200");

    rerender(<Button variant="outline">Outline</Button>);
    const outlineButton = screen.getByRole("button");
    expect(outlineButton).toHaveClass("border");
    expect(outlineButton).toHaveClass("border-gray-300");

    rerender(<Button variant="danger">Danger</Button>);
    const dangerButton = screen.getByRole("button");
    expect(dangerButton).toHaveClass("from-red-500");
    expect(dangerButton).toHaveClass("to-pink-500");
  });

  it("disables the button when isLoading is true", () => {
    render(<Button isLoading>Loading</Button>);
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
    expect(button).toHaveClass("opacity-80");
    expect(button).toHaveClass("cursor-wait");
  });

  it("disables the button when disabled is true", () => {
    render(<Button disabled>Disabled</Button>);
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
    expect(button).toHaveClass("opacity-60");
    expect(button).toHaveClass("cursor-not-allowed");
  });

  it("calls onClick handler when clicked", async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    const button = screen.getByRole("button");

    await userEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("does not call onClick handler when disabled", async () => {
    const handleClick = vi.fn();
    render(
      <Button onClick={handleClick} disabled>
        Click me
      </Button>
    );
    const button = screen.getByRole("button");

    await userEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it("renders a loading spinner when isLoading is true", () => {
    render(<Button isLoading>Loading</Button>);
    const svg = document.querySelector("svg");
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveClass("animate-spin");
  });
});
