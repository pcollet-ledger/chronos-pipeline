import { describe, it, expect } from "vitest";
import { darkTheme, lightTheme, statusColor } from "../theme";

describe("theme tokens", () => {
  it("darkTheme has all required keys", () => {
    expect(darkTheme.bg).toBeDefined();
    expect(darkTheme.bgCard).toBeDefined();
    expect(darkTheme.textPrimary).toBeDefined();
    expect(darkTheme.accent).toBeDefined();
    expect(darkTheme.success).toBeDefined();
    expect(darkTheme.error).toBeDefined();
  });

  it("lightTheme has all required keys", () => {
    expect(lightTheme.bg).toBeDefined();
    expect(lightTheme.bgCard).toBeDefined();
    expect(lightTheme.textPrimary).toBeDefined();
    expect(lightTheme.accent).toBeDefined();
    expect(lightTheme.success).toBeDefined();
    expect(lightTheme.error).toBeDefined();
  });

  it("dark and light themes have different backgrounds", () => {
    expect(darkTheme.bg).not.toBe(lightTheme.bg);
  });

  it("dark and light themes have different card backgrounds", () => {
    expect(darkTheme.bgCard).not.toBe(lightTheme.bgCard);
  });

  it("dark and light themes have different text colors", () => {
    expect(darkTheme.textPrimary).not.toBe(lightTheme.textPrimary);
  });
});

describe("statusColor", () => {
  it("returns success color for completed", () => {
    expect(statusColor(darkTheme, "completed")).toBe(darkTheme.statusCompleted);
  });

  it("returns error color for failed", () => {
    expect(statusColor(darkTheme, "failed")).toBe(darkTheme.statusFailed);
  });

  it("returns warning color for running", () => {
    expect(statusColor(darkTheme, "running")).toBe(darkTheme.statusRunning);
  });

  it("returns pending color for pending", () => {
    expect(statusColor(darkTheme, "pending")).toBe(darkTheme.statusPending);
  });

  it("returns cancelled color for cancelled", () => {
    expect(statusColor(darkTheme, "cancelled")).toBe(darkTheme.statusCancelled);
  });

  it("returns textMuted for unknown status", () => {
    expect(statusColor(darkTheme, "unknown")).toBe(darkTheme.textMuted);
  });

  it("works with light theme", () => {
    expect(statusColor(lightTheme, "completed")).toBe(lightTheme.statusCompleted);
  });

  it("returns textMuted for empty string", () => {
    expect(statusColor(darkTheme, "")).toBe(darkTheme.textMuted);
  });
});
