import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ProgressBar from "../components/ProgressBar";
import { ThemeProvider } from "../context/ThemeContext";

function wrap(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>);
}

describe("ProgressBar", () => {
  it("renders the progress bar container", () => {
    wrap(<ProgressBar value={50} />);
    expect(screen.getByTestId("progress-bar")).toBeDefined();
  });

  it("renders with correct aria attributes", () => {
    wrap(<ProgressBar value={75} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("75");
    expect(bar.getAttribute("aria-valuemin")).toBe("0");
    expect(bar.getAttribute("aria-valuemax")).toBe("100");
  });

  it("renders label when provided", () => {
    wrap(<ProgressBar value={50} label="Progress" />);
    expect(screen.getByText("Progress")).toBeDefined();
    expect(screen.getByText("50%")).toBeDefined();
  });

  it("does not render label when not provided", () => {
    wrap(<ProgressBar value={50} />);
    expect(screen.queryByText("50%")).toBeNull();
  });

  it("clamps value to 0 when negative", () => {
    wrap(<ProgressBar value={-10} label="Test" />);
    expect(screen.getByText("0%")).toBeDefined();
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("0");
  });

  it("clamps value to 100 when exceeding", () => {
    wrap(<ProgressBar value={150} label="Test" />);
    expect(screen.getByText("100%")).toBeDefined();
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("100");
  });

  it("renders fill element", () => {
    wrap(<ProgressBar value={60} />);
    expect(screen.getByTestId("progress-fill")).toBeDefined();
  });

  it("sets fill width based on value", () => {
    wrap(<ProgressBar value={30} />);
    const fill = screen.getByTestId("progress-fill");
    expect(fill.style.width).toBe("30%");
  });

  it("renders 0% fill for zero value", () => {
    wrap(<ProgressBar value={0} />);
    const fill = screen.getByTestId("progress-fill");
    expect(fill.style.width).toBe("0%");
  });

  it("renders 100% fill for full value", () => {
    wrap(<ProgressBar value={100} />);
    const fill = screen.getByTestId("progress-fill");
    expect(fill.style.width).toBe("100%");
  });

  it("rounds percentage display", () => {
    wrap(<ProgressBar value={33.7} label="Test" />);
    expect(screen.getByText("34%")).toBeDefined();
  });

  it("applies custom color to fill", () => {
    wrap(<ProgressBar value={50} color="#ff0000" />);
    const fill = screen.getByTestId("progress-fill");
    expect(fill.style.background).toBe("rgb(255, 0, 0)");
  });
});
