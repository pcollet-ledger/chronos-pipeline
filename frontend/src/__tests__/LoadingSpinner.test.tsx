import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import LoadingSpinner from "../components/LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders the spinner element", () => {
    render(<LoadingSpinner />);
    expect(screen.getByTestId("spinner")).toBeDefined();
  });

  it("renders with status role", () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole("status")).toBeDefined();
  });

  it("renders label when provided", () => {
    render(<LoadingSpinner label="Loading data..." />);
    expect(screen.getByText("Loading data...")).toBeDefined();
  });

  it("does not render label when not provided", () => {
    render(<LoadingSpinner />);
    expect(screen.queryByText("Loading data...")).toBeNull();
  });

  it("renders with custom size", () => {
    render(<LoadingSpinner size={64} />);
    const spinner = screen.getByTestId("spinner");
    expect(spinner.style.width).toBe("64px");
    expect(spinner.style.height).toBe("64px");
  });

  it("renders with default size", () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByTestId("spinner");
    expect(spinner.style.width).toBe("32px");
    expect(spinner.style.height).toBe("32px");
  });

  it("renders with empty label", () => {
    render(<LoadingSpinner label="" />);
    const status = screen.getByRole("status");
    expect(status).toBeDefined();
  });

  it("renders spinner with animation style", () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByTestId("spinner");
    expect(spinner.style.animation).toContain("spin");
  });

  it("renders with very long label", () => {
    const longLabel = "A".repeat(200);
    render(<LoadingSpinner label={longLabel} />);
    expect(screen.getByText(longLabel)).toBeDefined();
  });

  it("renders with size 0", () => {
    render(<LoadingSpinner size={0} />);
    const spinner = screen.getByTestId("spinner");
    expect(spinner.style.width).toBe("0px");
  });

  it("renders spinner with border-radius 50%", () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByTestId("spinner");
    expect(spinner.style.borderRadius).toBe("50%");
  });

  it("renders with very small size", () => {
    render(<LoadingSpinner size={1} />);
    const spinner = screen.getByTestId("spinner");
    expect(spinner.style.width).toBe("1px");
    expect(spinner.style.height).toBe("1px");
  });

  it("renders with large size", () => {
    render(<LoadingSpinner size={256} />);
    const spinner = screen.getByTestId("spinner");
    expect(spinner.style.width).toBe("256px");
    expect(spinner.style.height).toBe("256px");
  });
});
