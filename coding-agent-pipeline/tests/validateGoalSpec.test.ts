import { describe, expect, it } from "vitest";
import { InvalidGoalSpecError } from "../src/coding-agent-pipeline/errors.js";
import type { GoalSpec } from "../src/coding-agent-pipeline/goalSpec.js";
import { validateGoalSpec } from "../src/coding-agent-pipeline/validateGoalSpec.js";

function baseGoal(overrides: Partial<GoalSpec> = {}): GoalSpec {
  return {
    id: "goal-1",
    objective: "do the thing",
    targetFiles: ["a.ts"],
    scenario: {},
    acceptanceCriteria: [],
    constraints: [],
    maxAttempts: 3,
    ...overrides,
  };
}

describe("validateGoalSpec", () => {
  it("does not throw for a well-formed goal", () => {
    expect(() => validateGoalSpec(baseGoal())).not.toThrow();
  });

  it("rejects an empty id", () => {
    expect(() => validateGoalSpec(baseGoal({ id: "  " }))).toThrow(InvalidGoalSpecError);
  });

  it("rejects an empty objective", () => {
    expect(() => validateGoalSpec(baseGoal({ objective: "" }))).toThrow(InvalidGoalSpecError);
  });

  it("rejects a non-positive maxAttempts", () => {
    expect(() => validateGoalSpec(baseGoal({ maxAttempts: 0 }))).toThrow(InvalidGoalSpecError);
  });

  it("collects every violation into one error's reasons, including duplicate ids", () => {
    const goal = baseGoal({
      id: "",
      maxAttempts: -1,
      acceptanceCriteria: [
        { id: "dup", description: "", requiredCapability: "x", kind: "no-throws" },
        { id: "dup", description: "", requiredCapability: "x", kind: "no-throws" },
      ],
      constraints: [
        { id: "c", description: "", kind: "forbid-input-mutation" },
        { id: "c", description: "", kind: "forbid-input-mutation" },
      ],
    });

    let caught: unknown;
    try {
      validateGoalSpec(goal);
    } catch (err) {
      caught = err;
    }

    expect(caught).toBeInstanceOf(InvalidGoalSpecError);
    const invalid = caught as InvalidGoalSpecError;
    expect(invalid.reasons.length).toBeGreaterThanOrEqual(4);
    expect(invalid.reasons.some((r) => r.includes("id"))).toBe(true);
    expect(invalid.reasons.some((r) => r.includes("maxAttempts"))).toBe(true);
    expect(invalid.reasons.some((r) => r.includes("duplicate acceptanceCriteria"))).toBe(true);
    expect(invalid.reasons.some((r) => r.includes("duplicate constraint"))).toBe(true);
  });
});
