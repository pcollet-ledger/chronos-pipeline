import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ErrorBanner from "../components/ErrorBanner";

describe("ErrorBanner", () => {
  it("renders error message", () => {
    render(<ErrorBanner message="Something went wrong" />);
    expect(screen.getByText("Something went wrong")).toBeDefined();
  });

  it("renders with alert role", () => {
    render(<ErrorBanner message="Error" />);
    expect(screen.getByRole("alert")).toBeDefined();
  });

  it("renders retry button when onRetry is provided", () => {
    render(<ErrorBanner message="Error" onRetry={vi.fn()} />);
    expect(screen.getByText("Retry")).toBeDefined();
  });

  it("does not render retry button when onRetry is not provided", () => {
    render(<ErrorBanner message="Error" />);
    expect(screen.queryByText("Retry")).toBeNull();
  });

  it("renders dismiss button when onDismiss is provided", () => {
    render(<ErrorBanner message="Error" onDismiss={vi.fn()} />);
    expect(screen.getByLabelText("Dismiss error")).toBeDefined();
  });

  it("does not render dismiss button when onDismiss is not provided", () => {
    render(<ErrorBanner message="Error" />);
    expect(screen.queryByLabelText("Dismiss error")).toBeNull();
  });

  it("calls onRetry when retry button is clicked", () => {
    const onRetry = vi.fn();
    render(<ErrorBanner message="Error" onRetry={onRetry} />);
    fireEvent.click(screen.getByText("Retry"));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("calls onDismiss when dismiss button is clicked", () => {
    const onDismiss = vi.fn();
    render(<ErrorBanner message="Error" onDismiss={onDismiss} />);
    fireEvent.click(screen.getByLabelText("Dismiss error"));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("renders both retry and dismiss buttons", () => {
    render(
      <ErrorBanner message="Error" onRetry={vi.fn()} onDismiss={vi.fn()} />,
    );
    expect(screen.getByText("Retry")).toBeDefined();
    expect(screen.getByLabelText("Dismiss error")).toBeDefined();
  });

  it("renders long error message", () => {
    const longMsg = "Error: " + "x".repeat(500);
    render(<ErrorBanner message={longMsg} />);
    expect(screen.getByText(longMsg)).toBeDefined();
  });

  it("renders with empty message", () => {
    render(<ErrorBanner message="" />);
    expect(screen.getByRole("alert")).toBeDefined();
  });

  it("renders without any callbacks", () => {
    render(<ErrorBanner message="Standalone error" />);
    expect(screen.getByText("Standalone error")).toBeDefined();
    expect(screen.queryByText("Retry")).toBeNull();
    expect(screen.queryByLabelText("Dismiss error")).toBeNull();
  });
});
