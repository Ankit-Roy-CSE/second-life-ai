import "@testing-library/jest-dom";
import { configureAxe, toHaveNoViolations } from "jest-axe";
import { expect } from "vitest";

// Extend vitest's expect with jest-axe matchers so
// expect(results).toHaveNoViolations() works globally in every test file.
expect.extend(toHaveNoViolations);

// Configure axe with sensible defaults (can be overridden per-test).
configureAxe({
  rules: {
    // Disable color-contrast in jsdom since it can't compute computed styles.
    "color-contrast": { enabled: false },
  },
});
