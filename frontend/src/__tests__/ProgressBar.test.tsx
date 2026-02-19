import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ProgressBar from "../components/ProgressBar";

describe("ProgressBar", () => {
  it("renders with correct aria attributes", () => {
    render(<ProgressBar completed={3} total={10} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("30");
    expect(bar.getAttribute("aria-valuemin")).toBe("0");
    expect(bar.getAttribute("aria-valuemax")).toBe("100");
  });

  it("renders 0% when total is 0", () => {
    render(<ProgressBar completed={0} total={0} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("0");
  });

  it("renders 100% when all tasks are completed", () => {
    render(<ProgressBar completed={5} total={5} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("100");
  });

  it("renders 50% correctly", () => {
    render(<ProgressBar completed={1} total={2} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("50");
  });

  it("renders the fill element", () => {
    render(<ProgressBar completed={3} total={10} />);
    const fill = screen.getByTestId("progress-fill");
    expect(fill).toBeDefined();
    expect(fill.style.width).toBe("30%");
  });

  it("applies custom height", () => {
    render(<ProgressBar completed={1} total={2} height={16} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.style.height).toBe("16px");
  });

  it("uses status to determine color", () => {
    render(<ProgressBar completed={5} total={5} status="completed" />);
    const fill = screen.getByTestId("progress-fill");
    expect(fill.style.backgroundColor).toBeTruthy();
  });

  it("uses default status when not provided", () => {
    render(<ProgressBar completed={1} total={2} />);
    const fill = screen.getByTestId("progress-fill");
    expect(fill.style.backgroundColor).toBeTruthy();
  });

  it("rounds percentage to nearest integer", () => {
    render(<ProgressBar completed={1} total={3} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("33");
  });

  it("has accessible label", () => {
    render(<ProgressBar completed={7} total={10} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-label")).toBe("70% complete");
  });

  it("handles large numbers", () => {
    render(<ProgressBar completed={999} total={1000} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("100");
  });

  it("handles completed greater than total gracefully", () => {
    render(<ProgressBar completed={15} total={10} />);
    const bar = screen.getByRole("progressbar");
    expect(Number(bar.getAttribute("aria-valuenow"))).toBeGreaterThanOrEqual(100);
  });
});
