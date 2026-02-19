import { describe, it, expect } from "vitest";
import {
  lightTheme,
  darkTheme,
  getTheme,
  getStatusColor,
  statusColor,
} from "../theme";

describe("theme module", () => {
  it("lightTheme has all required tokens", () => {
    expect(lightTheme.bg).toBeTruthy();
    expect(lightTheme.surface).toBeTruthy();
    expect(lightTheme.text).toBeTruthy();
    expect(lightTheme.primary).toBeTruthy();
    expect(lightTheme.danger).toBeTruthy();
    expect(lightTheme.radius).toBeTruthy();
  });

  it("darkTheme has all required tokens", () => {
    expect(darkTheme.bg).toBeTruthy();
    expect(darkTheme.surface).toBeTruthy();
    expect(darkTheme.text).toBeTruthy();
    expect(darkTheme.primary).toBeTruthy();
    expect(darkTheme.danger).toBeTruthy();
    expect(darkTheme.radius).toBeTruthy();
  });

  it("lightTheme and darkTheme have different backgrounds", () => {
    expect(lightTheme.bg).not.toBe(darkTheme.bg);
  });

  it("lightTheme and darkTheme have different surface colors", () => {
    expect(lightTheme.surface).not.toBe(darkTheme.surface);
  });

  it("getTheme returns light theme for 'light'", () => {
    expect(getTheme("light")).toEqual(lightTheme);
  });

  it("getTheme returns dark theme for 'dark'", () => {
    expect(getTheme("dark")).toEqual(darkTheme);
  });

  it("getStatusColor returns correct color for completed", () => {
    expect(getStatusColor("completed")).toBe(statusColor.completed);
  });

  it("getStatusColor returns correct color for failed", () => {
    expect(getStatusColor("failed")).toBe(statusColor.failed);
  });

  it("getStatusColor returns correct color for running", () => {
    expect(getStatusColor("running")).toBe(statusColor.running);
  });

  it("getStatusColor returns fallback for unknown status", () => {
    expect(getStatusColor("unknown")).toBe("#6b7280");
  });

  it("getStatusColor is case-insensitive", () => {
    expect(getStatusColor("COMPLETED")).toBe(statusColor.completed);
  });

  it("statusColor has entries for all common statuses", () => {
    expect(statusColor.completed).toBeTruthy();
    expect(statusColor.running).toBeTruthy();
    expect(statusColor.pending).toBeTruthy();
    expect(statusColor.failed).toBeTruthy();
    expect(statusColor.cancelled).toBeTruthy();
  });
});
