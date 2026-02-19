import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThemeProvider } from "../ThemeContext";
import ProgressBar from "../components/ProgressBar";

function renderWithTheme(props: { percent: number; label?: string; height?: number }) {
  return render(
    <ThemeProvider>
      <ProgressBar {...props} />
    </ThemeProvider>,
  );
}

describe("ProgressBar", () => {
  it("renders the container", () => {
    renderWithTheme({ percent: 50 });
    expect(screen.getByTestId("progress-bar-container")).toBeDefined();
  });

  it("renders the fill bar with progressbar role", () => {
    renderWithTheme({ percent: 50 });
    expect(screen.getByRole("progressbar")).toBeDefined();
  });

  it("sets aria-valuenow to the percent value", () => {
    renderWithTheme({ percent: 75 });
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("75");
  });

  it("clamps percent to 0 minimum", () => {
    renderWithTheme({ percent: -10 });
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("0");
  });

  it("clamps percent to 100 maximum", () => {
    renderWithTheme({ percent: 150 });
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("100");
  });

  it("renders label when provided", () => {
    renderWithTheme({ percent: 50, label: "Loading..." });
    expect(screen.getByText("Loading...")).toBeDefined();
  });

  it("does not render label when not provided", () => {
    renderWithTheme({ percent: 50 });
    expect(screen.queryByText("Loading...")).toBeNull();
  });

  it("sets width style based on percent", () => {
    renderWithTheme({ percent: 60 });
    const fill = screen.getByTestId("progress-bar-fill");
    expect(fill.style.width).toBe("60%");
  });

  it("renders at 0%", () => {
    renderWithTheme({ percent: 0 });
    const fill = screen.getByTestId("progress-bar-fill");
    expect(fill.style.width).toBe("0%");
  });

  it("renders at 100%", () => {
    renderWithTheme({ percent: 100 });
    const fill = screen.getByTestId("progress-bar-fill");
    expect(fill.style.width).toBe("100%");
  });

  it("has aria-valuemin of 0", () => {
    renderWithTheme({ percent: 50 });
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuemin")).toBe("0");
  });

  it("has aria-valuemax of 100", () => {
    renderWithTheme({ percent: 50 });
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuemax")).toBe("100");
  });
});
