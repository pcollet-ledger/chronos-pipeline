import { describe, it, expect } from "vitest";
import {
  darkTheme,
  lightTheme,
  darkPalette,
  lightPalette,
  colors,
  spacing,
  borderRadius,
  fontSize,
  fontWeight,
  shadows,
  transitions,
} from "../styles/theme";

describe("theme", () => {
  it("exports dark and light themes", () => {
    expect(darkTheme).toBeDefined();
    expect(lightTheme).toBeDefined();
  });

  it("dark theme uses dark palette", () => {
    expect(darkTheme.palette).toBe(darkPalette);
  });

  it("light theme uses light palette", () => {
    expect(lightTheme.palette).toBe(lightPalette);
  });

  it("both themes share the same colors", () => {
    expect(darkTheme.colors).toBe(colors);
    expect(lightTheme.colors).toBe(colors);
  });

  it("both themes share spacing", () => {
    expect(darkTheme.spacing).toBe(spacing);
    expect(lightTheme.spacing).toBe(spacing);
  });

  it("both themes share borderRadius", () => {
    expect(darkTheme.borderRadius).toBe(borderRadius);
    expect(lightTheme.borderRadius).toBe(borderRadius);
  });

  it("both themes share fontSize", () => {
    expect(darkTheme.fontSize).toBe(fontSize);
    expect(lightTheme.fontSize).toBe(fontSize);
  });

  it("both themes share fontWeight", () => {
    expect(darkTheme.fontWeight).toBe(fontWeight);
    expect(lightTheme.fontWeight).toBe(fontWeight);
  });

  it("both themes share shadows", () => {
    expect(darkTheme.shadows).toBe(shadows);
    expect(lightTheme.shadows).toBe(shadows);
  });

  it("both themes share transitions", () => {
    expect(darkTheme.transitions).toBe(transitions);
    expect(lightTheme.transitions).toBe(transitions);
  });

  it("dark palette has dark background", () => {
    expect(darkPalette.background).toBe("#0f172a");
  });

  it("light palette has light background", () => {
    expect(lightPalette.background).toBe("#f8fafc");
  });

  it("colors has primary", () => {
    expect(colors.primary).toBe("#2563eb");
  });

  it("spacing has expected values", () => {
    expect(spacing.xs).toBe("4px");
    expect(spacing.sm).toBe("8px");
    expect(spacing.md).toBe("16px");
    expect(spacing.lg).toBe("24px");
    expect(spacing.xl).toBe("32px");
    expect(spacing.xxl).toBe("48px");
  });

  it("borderRadius has expected values", () => {
    expect(borderRadius.sm).toBe("4px");
    expect(borderRadius.md).toBe("8px");
    expect(borderRadius.lg).toBe("12px");
    expect(borderRadius.full).toBe("9999px");
  });
});
