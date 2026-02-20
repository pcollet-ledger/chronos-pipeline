import { describe, it, expect } from "vitest";
import {
  lightTheme,
  darkTheme,
  getTheme,
  getStatusColor,
  statusColor,
  spacing,
  radii,
  fontSize,
  fontWeight,
  shadows,
  transition,
  palette,
  priorityColor,
  getPriorityColor,
  formatDuration,
} from "../theme";
import type {
  ThemeTokens,
  SpacingScale,
  Radii,
  FontSize,
  FontWeight,
  Shadows,
  Transition,
  Palette,
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
    expect(getStatusColor("unknown")).toBe(palette.secondary.base);
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

describe("spacing scale", () => {
  it("has all required scale values from xs to xxl", () => {
    const keys: (keyof SpacingScale)[] = ["xs", "sm", "md", "lg", "xl", "xxl"];
    for (const key of keys) {
      expect(spacing[key]).toBeTruthy();
      expect(spacing[key]).toMatch(/^\d+px$/);
    }
  });

  it("values increase monotonically", () => {
    const values = [spacing.xs, spacing.sm, spacing.md, spacing.lg, spacing.xl, spacing.xxl];
    const nums = values.map((v) => parseInt(v, 10));
    for (let i = 1; i < nums.length; i++) {
      expect(nums[i]).toBeGreaterThan(nums[i - 1]!);
    }
  });
});

describe("radii", () => {
  it("has sm, md, lg, xl, and full values", () => {
    expect(radii.sm).toBeTruthy();
    expect(radii.md).toBeTruthy();
    expect(radii.lg).toBeTruthy();
    expect(radii.xl).toBeTruthy();
    expect(radii.full).toBeTruthy();
  });

  it("full is a large value for pill shapes", () => {
    expect(parseInt(radii.full, 10)).toBeGreaterThan(100);
  });
});

describe("fontSize", () => {
  it("has all scale values", () => {
    const keys: (keyof FontSize)[] = ["xs", "sm", "md", "lg", "xl", "xxl", "h1", "h2"];
    for (const key of keys) {
      expect(fontSize[key]).toBeTruthy();
      expect(fontSize[key]).toMatch(/^\d+px$/);
    }
  });

  it("h2 is the largest", () => {
    expect(parseInt(fontSize.h2, 10)).toBeGreaterThan(parseInt(fontSize.h1, 10));
  });
});

describe("fontWeight", () => {
  it("has normal, medium, semibold, and bold", () => {
    expect(fontWeight.normal).toBe(400);
    expect(fontWeight.medium).toBe(500);
    expect(fontWeight.semibold).toBe(600);
    expect(fontWeight.bold).toBe(700);
  });

  it("values increase monotonically", () => {
    expect(fontWeight.medium).toBeGreaterThan(fontWeight.normal);
    expect(fontWeight.semibold).toBeGreaterThan(fontWeight.medium);
    expect(fontWeight.bold).toBeGreaterThan(fontWeight.semibold);
  });
});

describe("shadows", () => {
  it("has sm, md, lg for light mode", () => {
    expect(shadows.sm).toBeTruthy();
    expect(shadows.md).toBeTruthy();
    expect(shadows.lg).toBeTruthy();
  });

  it("has dark variants", () => {
    expect(shadows.dark.sm).toBeTruthy();
    expect(shadows.dark.md).toBeTruthy();
    expect(shadows.dark.lg).toBeTruthy();
  });

  it("dark shadows have higher opacity than light", () => {
    const lightOpacity = parseFloat(shadows.md.match(/[\d.]+\)$/)?.[0] ?? "0");
    const darkOpacity = parseFloat(shadows.dark.md.match(/[\d.]+\)$/)?.[0] ?? "0");
    expect(darkOpacity).toBeGreaterThan(lightOpacity);
  });
});

describe("transition", () => {
  it("has fast, normal, and slow durations", () => {
    expect(transition.fast).toContain("ms");
    expect(transition.normal).toContain("ms");
    expect(transition.slow).toContain("ms");
  });

  it("fast is shorter than normal which is shorter than slow", () => {
    const parse = (t: string) => parseInt(t, 10);
    expect(parse(transition.fast)).toBeLessThan(parse(transition.normal));
    expect(parse(transition.normal)).toBeLessThan(parse(transition.slow));
  });
});

describe("palette", () => {
  it("has all six colour groups", () => {
    const groups: (keyof Palette)[] = ["primary", "secondary", "error", "warning", "success", "info"];
    for (const group of groups) {
      expect(palette[group].base).toBeTruthy();
      expect(palette[group].light).toBeTruthy();
      expect(palette[group].dark).toBeTruthy();
    }
  });

  it("each group has base, light, and dark variants as hex colours", () => {
    const hexRegex = /^#[0-9a-fA-F]{6}$/;
    for (const group of Object.values(palette)) {
      expect(group.base).toMatch(hexRegex);
      expect(group.light).toMatch(hexRegex);
      expect(group.dark).toMatch(hexRegex);
    }
  });
});

describe("priorityColor", () => {
  it("has entries for low, medium, high, critical", () => {
    expect(priorityColor.low).toBeTruthy();
    expect(priorityColor.medium).toBeTruthy();
    expect(priorityColor.high).toBeTruthy();
    expect(priorityColor.critical).toBeTruthy();
  });

  it("getPriorityColor returns correct color for known priorities", () => {
    expect(getPriorityColor("high")).toBe(priorityColor.high);
    expect(getPriorityColor("low")).toBe(priorityColor.low);
  });

  it("getPriorityColor is case-insensitive", () => {
    expect(getPriorityColor("HIGH")).toBe(priorityColor.high);
  });

  it("getPriorityColor returns fallback for unknown priority", () => {
    expect(getPriorityColor("unknown")).toBe(palette.secondary.base);
  });
});

describe("formatDuration", () => {
  it("formats milliseconds", () => {
    expect(formatDuration(500)).toBe("500ms");
  });

  it("formats seconds", () => {
    expect(formatDuration(1500)).toBe("1.5s");
  });

  it("formats minutes", () => {
    expect(formatDuration(90000)).toBe("1.5m");
  });

  it("formats zero", () => {
    expect(formatDuration(0)).toBe("0ms");
  });
});

describe("ThemeTokens extended fields", () => {
  it("lightTheme has new extended tokens", () => {
    expect(lightTheme.surfaceAlt).toBeTruthy();
    expect(lightTheme.borderSubtle).toBeTruthy();
    expect(lightTheme.textMuted).toBeTruthy();
    expect(lightTheme.accent).toBeTruthy();
    expect(lightTheme.shadowLg).toBeTruthy();
    expect(lightTheme.tagBg).toBeTruthy();
    expect(lightTheme.tagText).toBeTruthy();
    expect(lightTheme.inputBg).toBeTruthy();
    expect(lightTheme.inputBorder).toBeTruthy();
    expect(lightTheme.tableBorder).toBeTruthy();
    expect(lightTheme.highlight).toBeTruthy();
  });

  it("darkTheme has new extended tokens", () => {
    expect(darkTheme.surfaceAlt).toBeTruthy();
    expect(darkTheme.borderSubtle).toBeTruthy();
    expect(darkTheme.textMuted).toBeTruthy();
    expect(darkTheme.accent).toBeTruthy();
    expect(darkTheme.shadowLg).toBeTruthy();
    expect(darkTheme.tagBg).toBeTruthy();
    expect(darkTheme.tagText).toBeTruthy();
    expect(darkTheme.inputBg).toBeTruthy();
    expect(darkTheme.inputBorder).toBeTruthy();
    expect(darkTheme.tableBorder).toBeTruthy();
    expect(darkTheme.highlight).toBeTruthy();
  });

  it("light and dark themes differ on surfaceAlt", () => {
    expect(lightTheme.surfaceAlt).not.toBe(darkTheme.surfaceAlt);
  });

  it("light and dark themes differ on tagBg", () => {
    expect(lightTheme.tagBg).not.toBe(darkTheme.tagBg);
  });
});

describe("type exports compile correctly", () => {
  it("ThemeTokens type is usable", () => {
    const t: ThemeTokens = lightTheme;
    expect(t.bg).toBeTruthy();
  });

  it("SpacingScale type is usable", () => {
    const s: SpacingScale = spacing;
    expect(s.xs).toBeTruthy();
  });

  it("Radii type is usable", () => {
    const r: Radii = radii;
    expect(r.sm).toBeTruthy();
  });

  it("FontSize type is usable", () => {
    const f: FontSize = fontSize;
    expect(f.xs).toBeTruthy();
  });

  it("FontWeight type is usable", () => {
    const f: FontWeight = fontWeight;
    expect(f.normal).toBe(400);
  });

  it("Shadows type is usable", () => {
    const s: Shadows = shadows;
    expect(s.sm).toBeTruthy();
  });

  it("Transition type is usable", () => {
    const t: Transition = transition;
    expect(t.fast).toBeTruthy();
  });

  it("Palette type is usable", () => {
    const p: Palette = palette;
    expect(p.primary.base).toBeTruthy();
  });
});
