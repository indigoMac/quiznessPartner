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
    const button = screen.getByText("Primary");
    expect(button).toHaveClass("bg-blue-600");

    rerender(<Button variant="secondary">Secondary</Button>);
    const secondaryButton = screen.getByText("Secondary");
    expect(secondaryButton).toHaveClass("bg-gray-200");

    rerender(<Button variant="outline">Outline</Button>);
    const outlineButton = screen.getByText("Outline");
    expect(outlineButton).toHaveClass("border");
    expect(outlineButton).toHaveClass("border-gray-300");

    rerender(<Button variant="danger">Danger</Button>);
    const dangerButton = screen.getByText("Danger");
    expect(dangerButton).toHaveClass("bg-red-600");
  });

  it("disables the button when isLoading is true", () => {
    render(<Button isLoading>Loading</Button>);
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
    expect(button).toHaveClass("opacity-70");
  });

  it("disables the button when disabled is true", () => {
    render(<Button disabled>Disabled</Button>);
    const button = screen.getByText("Disabled");
    expect(button).toBeDisabled();
    expect(button).toHaveClass("opacity-50");
  });

  it("calls onClick handler when clicked", async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    const button = screen.getByText("Click me");

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
    const button = screen.getByText("Click me");

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
