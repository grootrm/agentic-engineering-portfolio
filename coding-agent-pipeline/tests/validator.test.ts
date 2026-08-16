import { describe, expect, it } from "vitest";
import type { ExecutionResult } from "../src/coding-agent-pipeline/executor.js";
import type { AcceptanceCheck, Constraint, GoalSpec } from "../src/coding-agent-pipeline/goalSpec.js";
import type { JsonObject } from "../src/coding-agent-pipeline/jsonUtils.js";
import { validate } from "../src/coding-agent-pipeline/validator.js";

function goalWith(acceptanceCriteria: AcceptanceCheck[], constraints: Constraint[] = []): GoalSpec {
  return {
    id: "g",
    objective: "",
    targetFiles: [],
    scenario: null,
    acceptanceCriteria,
    constraints,
    maxAttempts: 3,
  };
}

function execution(overrides: Partial<ExecutionResult> = {}): ExecutionResult {
  return {
    attempt: 1,
    strategyName: "s",
    output: { a: { b: 1 } } as JsonObject,
    thrownErrorName: null,
    inputMutated: false,
    ...overrides,
  };
}

function outcomeFor(report: ReturnType<typeof validate>, id: string) {
  const outcome = report.outcomes.find((o) => o.id === id);
  if (!outcome) throw new Error(`no outcome for id "${id}"`);
  return outcome;
}

describe("validate — acceptance checks", () => {
  it("path-equals passes on match and fails on mismatch", () => {
    const check: AcceptanceCheck = { id: "c", description: "", requiredCapability: "x", kind: "path-equals", path: ["a", "b"], expected: 1 };
    expect(outcomeFor(validate(goalWith([check]), execution()), "c").passed).toBe(true);
    expect(outcomeFor(validate(goalWith([check]), execution({ output: { a: { b: 2 } } })), "c").passed).toBe(false);
  });

  it("path-absent passes when the path is missing and fails when present", () => {
    const check: AcceptanceCheck = { id: "c", description: "", requiredCapability: "x", kind: "path-absent", path: ["a", "missing"] };
    expect(outcomeFor(validate(goalWith([check]), execution()), "c").passed).toBe(true);
    const present: AcceptanceCheck = { id: "c", description: "", requiredCapability: "x", kind: "path-absent", path: ["a", "b"] };
    expect(outcomeFor(validate(goalWith([present]), execution()), "c").passed).toBe(false);
  });

  it("path-type passes on the expected JSON type and fails otherwise", () => {
    const check: AcceptanceCheck = { id: "c", description: "", requiredCapability: "x", kind: "path-type", path: ["a"], expectedType: "object" };
    expect(outcomeFor(validate(goalWith([check]), execution()), "c").passed).toBe(true);
    const wrong: AcceptanceCheck = { id: "c", description: "", requiredCapability: "x", kind: "path-type", path: ["a"], expectedType: "array" };
    expect(outcomeFor(validate(goalWith([wrong]), execution()), "c").passed).toBe(false);
  });

  it("throws passes only when an error was thrown (optionally matching expectedErrorName)", () => {
    const check: AcceptanceCheck = { id: "c", description: "", requiredCapability: "x", kind: "throws", expectedErrorName: "RangeError" };
    expect(outcomeFor(validate(goalWith([check]), execution({ output: null, thrownErrorName: "RangeError" })), "c").passed).toBe(true);
    expect(outcomeFor(validate(goalWith([check]), execution()), "c").passed).toBe(false);
    expect(outcomeFor(validate(goalWith([check]), execution({ output: null, thrownErrorName: "TypeError" })), "c").passed).toBe(false);
  });

  it("no-throws passes only when no error was thrown", () => {
    const check: AcceptanceCheck = { id: "c", description: "", requiredCapability: "x", kind: "no-throws" };
    expect(outcomeFor(validate(goalWith([check]), execution()), "c").passed).toBe(true);
    expect(outcomeFor(validate(goalWith([check]), execution({ output: null, thrownErrorName: "Error" })), "c").passed).toBe(false);
  });
});

describe("validate — constraints", () => {
  it("forbid-input-mutation reflects execution.inputMutated", () => {
    const constraint: Constraint = { id: "c", description: "", kind: "forbid-input-mutation" };
    expect(outcomeFor(validate(goalWith([], [constraint]), execution({ inputMutated: false })), "c").passed).toBe(true);
    expect(outcomeFor(validate(goalWith([], [constraint]), execution({ inputMutated: true })), "c").passed).toBe(false);
  });

  it("protected-path-immutable passes when the path equals the expected value", () => {
    const constraint: Constraint = { id: "c", description: "", kind: "protected-path-immutable", path: ["a", "b"], expected: 1 };
    expect(outcomeFor(validate(goalWith([], [constraint]), execution()), "c").passed).toBe(true);
    expect(outcomeFor(validate(goalWith([], [constraint]), execution({ output: { a: { b: 2 } } })), "c").passed).toBe(false);
  });

  it("max-output-depth passes when within budget and fails when exceeded", () => {
    const constraint: Constraint = { id: "c", description: "", kind: "max-output-depth", maxDepth: 5 };
    expect(outcomeFor(validate(goalWith([], [constraint]), execution()), "c").passed).toBe(true);
    const tight: Constraint = { id: "c", description: "", kind: "max-output-depth", maxDepth: 0 };
    expect(outcomeFor(validate(goalWith([], [tight]), execution()), "c").passed).toBe(false);
  });
});
