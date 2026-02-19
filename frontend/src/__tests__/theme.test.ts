import { describe, it, expect } from "vitest";
import theme, {
  colors,
  fontSizes,
  fontWeights,
  priorityColors,
  radii,
  shadows,
  spacing,
  statusColors,
  transitions,
} from "../styles/theme";
import type { Theme } from "../styles/theme";

describe("theme module", () => {
  // ---- composite object ---------------------------------------------------

  it("exports a default theme object with all sections", () => {
    expect(theme).toBeDefined();
    expect(theme.colors).toBe(colors);
    expect(theme.spacing).toBe(spacing);
    expect(theme.radii).toBe(radii);
    expect(theme.fontSizes).toBe(fontSizes);
    expect(theme.fontWeights).toBe(fontWeights);
    expect(theme.shadows).toBe(shadows);
    expect(theme.transitions).toBe(transitions);
    expect(theme.statusColors).toBe(statusColors);
    expect(theme.priorityColors).toBe(priorityColors);
  });

  it("Theme type is assignable from the default export", () => {
    const t: Theme = theme;
    expect(t).toBe(theme);
  });

  // ---- colours ------------------------------------------------------------

  it("provides primary colour variants", () => {
    expect(colors.primary.light).toBe("#60a5fa");
    expect(colors.primary.main).toBe("#2563eb");
    expect(colors.primary.dark).toBe("#1e40af");
  });

  it("provides secondary colour variants", () => {
    expect(colors.secondary.light).toBe("#c4b5fd");
    expect(colors.secondary.main).toBe("#a78bfa");
    expect(colors.secondary.dark).toBe("#7c3aed");
  });

  it("provides error colour variants including bg", () => {
    expect(colors.error.light).toBe("#fca5a5");
    expect(colors.error.main).toBe("#ef4444");
    expect(colors.error.dark).toBe("#dc2626");
    expect(colors.error.bg).toBe("#7f1d1d");
  });

  it("provides warning colour variants", () => {
    expect(colors.warning.light).toBe("#fde68a");
    expect(colors.warning.main).toBe("#eab308");
    expect(colors.warning.dark).toBe("#ca8a04");
  });

  it("provides success colour variants", () => {
    expect(colors.success.light).toBe("#86efac");
    expect(colors.success.main).toBe("#22c55e");
    expect(colors.success.dark).toBe("#059669");
  });

  it("provides info colour variants", () => {
    expect(colors.info.light).toBe("#67e8f9");
    expect(colors.info.main).toBe("#38bdf8");
    expect(colors.info.dark).toBe("#0ea5e9");
  });

  it("provides a full neutral scale from 50 to 900", () => {
    const keys = Object.keys(colors.neutral);
    expect(keys).toEqual(
      expect.arrayContaining(["50", "100", "200", "300", "400", "500", "600", "700", "800", "900"]),
    );
    for (const val of Object.values(colors.neutral)) {
      expect(val).toMatch(/^#[0-9a-f]{6}$/);
    }
  });

  // ---- status & priority colours ------------------------------------------

  it("maps all workflow statuses to colours", () => {
    expect(statusColors.completed).toBe(colors.success.main);
    expect(statusColors.failed).toBe(colors.error.main);
    expect(statusColors.running).toBe(colors.warning.main);
    expect(statusColors.pending).toBe(colors.neutral[500]);
    expect(statusColors.cancelled).toBe(colors.muted);
  });

  it("maps all priority levels to colours", () => {
    expect(priorityColors.low).toBe(colors.neutral[500]);
    expect(priorityColors.medium).toBe(colors.primary.light);
    expect(priorityColors.high).toBe(colors.warning.main);
    expect(priorityColors.critical).toBe(colors.error.main);
  });

  // ---- spacing ------------------------------------------------------------

  it("provides a spacing scale from xs to xxxxl", () => {
    expect(spacing.xs).toBe("4px");
    expect(spacing.sm).toBe("8px");
    expect(spacing.md).toBe("12px");
    expect(spacing.lg).toBe("16px");
    expect(spacing.xl).toBe("20px");
    expect(spacing.xxl).toBe("24px");
    expect(spacing.xxxl).toBe("32px");
    expect(spacing.xxxxl).toBe("40px");
  });

  it("spacing values are valid CSS lengths", () => {
    for (const val of Object.values(spacing)) {
      expect(val).toMatch(/^\d+px$/);
    }
  });

  // ---- radii --------------------------------------------------------------

  it("provides border-radius tokens", () => {
    expect(radii.sm).toBe("4px");
    expect(radii.md).toBe("6px");
    expect(radii.lg).toBe("8px");
    expect(radii.xl).toBe("12px");
    expect(radii.full).toBe("50%");
  });

  // ---- typography ---------------------------------------------------------

  it("provides font size tokens", () => {
    expect(fontSizes.xs).toBe("11px");
    expect(fontSizes.sm).toBe("12px");
    expect(fontSizes.md).toBe("13px");
    expect(fontSizes.base).toBe("14px");
    expect(fontSizes.lg).toBe("16px");
    expect(fontSizes.xl).toBe("18px");
    expect(fontSizes.xxl).toBe("20px");
    expect(fontSizes.xxxl).toBe("28px");
  });

  it("provides font weight tokens as numbers", () => {
    expect(fontWeights.normal).toBe(400);
    expect(fontWeights.medium).toBe(500);
    expect(fontWeights.semibold).toBe(600);
    expect(fontWeights.bold).toBe(700);
  });

  // ---- shadows ------------------------------------------------------------

  it("provides shadow definitions as strings", () => {
    expect(typeof shadows.sm).toBe("string");
    expect(typeof shadows.md).toBe("string");
    expect(typeof shadows.lg).toBe("string");
    expect(typeof shadows.xl).toBe("string");
    for (const val of Object.values(shadows)) {
      expect(val).toContain("rgba");
    }
  });

  // ---- transitions --------------------------------------------------------

  it("provides transition duration tokens", () => {
    expect(transitions.fast).toBe("150ms ease");
    expect(transitions.normal).toBe("250ms ease");
    expect(transitions.slow).toBe("400ms ease");
  });

  it("all transition values contain 'ms'", () => {
    for (const val of Object.values(transitions)) {
      expect(val).toContain("ms");
    }
  });
});
