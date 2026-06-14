// Sanity test — verifies the test framework (Vitest + jest-dom + jest-axe + fast-check) is
// configured correctly. Safe to delete once the real test suite is in place.
import { expect, test } from "vitest";
import * as fc from "fast-check";

test("jest-dom matchers are available", () => {
  const div = document.createElement("div");
  document.body.appendChild(div);
  expect(div).toBeInTheDocument();
  document.body.removeChild(div);
});

test("fast-check generates booleans", () => {
  fc.assert(
    fc.property(fc.boolean(), (b) => {
      return typeof b === "boolean";
    }),
    { numRuns: 50 }
  );
});
