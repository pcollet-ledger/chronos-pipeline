import { describe, it, expect } from "vitest";
import { colors, statusColors, spacing, radii, fontSizes, formatDuration } from "../theme";

describe("theme tokens", () => {
  it("exports color constants", () => {
    expect(colors.bg).toBe("#0f172a");
    expect(colors.primary).toBe("#2563eb");
    expect(colors.success).toBe("#22c55e");
    expect(colors.error).toBe("#ef4444");
  });

  it("exports status colors for all statuses", () => {
    expect(statusColors["completed"]).toBe(colors.success);
    expect(statusColors["failed"]).toBe(colors.error);
    expect(statusColors["running"]).toBe(colors.warning);
    expect(statusColors["pending"]).toBe(colors.textMuted);
    expect(statusColors["cancelled"]).toBe(colors.cancelled);
  });

  it("exports spacing tokens", () => {
    expect(spacing.xs).toBe("4px");
    expect(spacing.xxxl).toBe("32px");
  });

  it("exports radii tokens", () => {
    expect(radii.sm).toBe("4px");
    expect(radii.xl).toBe("12px");
  });

  it("exports font size tokens", () => {
    expect(fontSizes.xs).toBe("11px");
    expect(fontSizes.heading).toBe("28px");
  });
});

describe("formatDuration", () => {
  it("formats milliseconds", () => {
    expect(formatDuration(500)).toBe("500ms");
  });

  it("formats zero", () => {
    expect(formatDuration(0)).toBe("0ms");
  });

  it("formats seconds", () => {
    expect(formatDuration(1500)).toBe("1.5s");
  });

  it("formats exactly 1 second", () => {
    expect(formatDuration(1000)).toBe("1.0s");
  });

  it("formats minutes", () => {
    expect(formatDuration(90000)).toBe("1.5m");
  });

  it("formats hours", () => {
    expect(formatDuration(3600000)).toBe("1.0h");
  });

  it("formats sub-millisecond as 0ms", () => {
    expect(formatDuration(0.5)).toBe("1ms");
  });

  it("formats 59 seconds", () => {
    expect(formatDuration(59000)).toBe("59.0s");
  });

  it("formats 60 seconds as 1.0m", () => {
    expect(formatDuration(60000)).toBe("1.0m");
  });

  it("formats 59 minutes", () => {
    expect(formatDuration(3540000)).toBe("59.0m");
  });
});
