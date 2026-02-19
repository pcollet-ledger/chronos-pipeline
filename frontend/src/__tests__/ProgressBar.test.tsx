import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ProgressBar from "../components/ProgressBar";

describe("ProgressBar", () => {
  it("renders the container", () => {
    render(<ProgressBar value={50} />);
    expect(screen.getByTestId("progress-bar-container")).toBeDefined();
  });

  it("renders a progressbar role element", () => {
    render(<ProgressBar value={50} />);
    expect(screen.getByRole("progressbar")).toBeDefined();
  });

  it("sets aria-valuenow to the clamped value", () => {
    render(<ProgressBar value={75} />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("75");
  });

  it("sets aria-valuemin to 0", () => {
    render(<ProgressBar value={50} />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuemin")).toBe("0");
  });

  it("sets aria-valuemax to the max prop", () => {
    render(<ProgressBar value={50} max={200} />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuemax")).toBe("200");
  });

  it("defaults max to 100", () => {
    render(<ProgressBar value={50} />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuemax")).toBe("100");
  });

  it("clamps value to 0 when negative", () => {
    render(<ProgressBar value={-10} />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("0");
  });

  it("clamps value to max when exceeding", () => {
    render(<ProgressBar value={150} max={100} />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("100");
  });

  it("renders the fill element", () => {
    render(<ProgressBar value={50} />);
    expect(screen.getByTestId("progress-fill")).toBeDefined();
  });

  it("sets fill width to correct percentage", () => {
    render(<ProgressBar value={25} max={100} />);
    expect(screen.getByTestId("progress-fill").style.width).toBe("25%");
  });

  it("renders 0% width when value is 0", () => {
    render(<ProgressBar value={0} />);
    expect(screen.getByTestId("progress-fill").style.width).toBe("0%");
  });

  it("renders 100% width when value equals max", () => {
    render(<ProgressBar value={100} />);
    expect(screen.getByTestId("progress-fill").style.width).toBe("100%");
  });

  it("renders label when provided", () => {
    render(<ProgressBar value={50} label="Loading..." />);
    expect(screen.getByTestId("progress-label")).toBeDefined();
    expect(screen.getByText("Loading...")).toBeDefined();
  });

  it("does not render label when not provided", () => {
    render(<ProgressBar value={50} />);
    expect(screen.queryByTestId("progress-label")).toBeNull();
  });

  it("shows percent when showPercent is true", () => {
    render(<ProgressBar value={75} showPercent />);
    expect(screen.getByTestId("progress-percent")).toBeDefined();
    expect(screen.getByText("75%")).toBeDefined();
  });

  it("does not show percent by default", () => {
    render(<ProgressBar value={50} />);
    expect(screen.queryByTestId("progress-percent")).toBeNull();
  });

  it("renders both label and percent together", () => {
    render(<ProgressBar value={60} label="Progress" showPercent />);
    expect(screen.getByText("Progress")).toBeDefined();
    expect(screen.getByText("60%")).toBeDefined();
  });

  it("handles max of 0 gracefully", () => {
    render(<ProgressBar value={50} max={0} showPercent />);
    expect(screen.getByText("0%")).toBeDefined();
  });

  it("calculates percent with custom max", () => {
    render(<ProgressBar value={5} max={10} showPercent />);
    expect(screen.getByText("50%")).toBeDefined();
  });

  it("applies custom height", () => {
    render(<ProgressBar value={50} height={16} />);
    expect(screen.getByRole("progressbar").style.height).toBe("16px");
  });

  it("applies custom color to fill", () => {
    render(<ProgressBar value={50} color="#ff0000" />);
    expect(screen.getByTestId("progress-fill").style.background).toBe("rgb(255, 0, 0)");
  });

  it("applies custom background color", () => {
    render(<ProgressBar value={50} bgColor="#000000" />);
    expect(screen.getByRole("progressbar").style.background).toBe("rgb(0, 0, 0)");
  });

  it("renders with value equal to 1 out of 3", () => {
    render(<ProgressBar value={1} max={3} showPercent />);
    expect(screen.getByText("33%")).toBeDefined();
  });
});
