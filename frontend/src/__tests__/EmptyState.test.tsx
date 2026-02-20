import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import EmptyState from "../components/EmptyState";

describe("EmptyState", () => {
  it("renders message", () => {
    render(<EmptyState message="No items found" />);
    expect(screen.getByText("No items found")).toBeDefined();
  });

  it("renders action button when both label and handler are provided", () => {
    render(
      <EmptyState
        message="Empty"
        actionLabel="Create"
        onAction={vi.fn()}
      />,
    );
    expect(screen.getByText("Create")).toBeDefined();
  });

  it("does not render action button when actionLabel is missing", () => {
    render(<EmptyState message="Empty" onAction={vi.fn()} />);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("does not render action button when onAction is missing", () => {
    render(<EmptyState message="Empty" actionLabel="Create" />);
    expect(screen.queryByText("Create")).toBeNull();
  });

  it("calls onAction when button is clicked", () => {
    const onAction = vi.fn();
    render(
      <EmptyState message="Empty" actionLabel="Create" onAction={onAction} />,
    );
    fireEvent.click(screen.getByText("Create"));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it("renders the icon placeholder", () => {
    render(<EmptyState message="Empty" />);
    expect(screen.getByText("○")).toBeDefined();
  });

  it("renders with long message", () => {
    const longMsg = "No data available. " + "x".repeat(300);
    render(<EmptyState message={longMsg} />);
    expect(screen.getByText(longMsg)).toBeDefined();
  });

  it("renders with empty message", () => {
    render(<EmptyState message="" />);
    expect(screen.getByText("○")).toBeDefined();
  });

  it("renders without any optional props", () => {
    render(<EmptyState message="Nothing here" />);
    expect(screen.getByText("Nothing here")).toBeDefined();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("renders action button with long label", () => {
    render(
      <EmptyState
        message="Empty"
        actionLabel={"A".repeat(100)}
        onAction={vi.fn()}
      />,
    );
    expect(screen.getByText("A".repeat(100))).toBeDefined();
  });

  it("does not call onAction without user interaction", () => {
    const onAction = vi.fn();
    render(
      <EmptyState message="Empty" actionLabel="Go" onAction={onAction} />,
    );
    expect(onAction).not.toHaveBeenCalled();
  });

  it("renders icon with aria-hidden", () => {
    render(<EmptyState message="Empty" />);
    const icon = screen.getByText("○");
    expect(icon.getAttribute("aria-hidden")).toBe("true");
  });

  it("renders message with special characters", () => {
    const msg = "No items found <script>alert('xss')</script>";
    render(<EmptyState message={msg} />);
    expect(screen.getByText(msg)).toBeDefined();
  });
});
