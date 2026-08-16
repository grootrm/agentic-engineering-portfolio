import { describe, expect, it } from "vitest";
import { InvalidGoalSpecError } from "../src/coding-agent-pipeline/errors.js";
import type { StrategyFn } from "../src/coding-agent-pipeline/executor.js";
import type { GoalSpec } from "../src/coding-agent-pipeline/goalSpec.js";
import type { JsonObject } from "../src/coding-agent-pipeline/jsonUtils.js";
import { runGoal } from "../src/coding-agent-pipeline/orchestrator.js";
import type { Strategy } from "../src/coding-agent-pipeline/strategy.js";

const alwaysFail: StrategyFn<JsonObject, JsonObject> = (input) => ({ ...input, result: "fail" });
const alwaysPass: StrategyFn<JsonObject, JsonObject> = (input) => ({ ...input, result: "pass" });

function goal(overrides: Partial<GoalSpec<JsonObject>> = {}): GoalSpec<JsonObject> {
  return {
    id: "fixture-goal",
    objective: "reach result: pass",
    targetFiles: ["fixture.ts"],
    scenario: {},
    acceptanceCriteria: [{ id: "result-passes", description: "", requiredCapability: "cap", kind: "path-equals", path: ["result"], expected: "pass" }],
    constraints: [],
    maxAttempts: 3,
    ...overrides,
  };
}

describe("runGoal", () => {
  it("reaches done on the first attempt when the cheapest strategy already satisfies the goal", () => {
    const catalog: Strategy[] = [{ name: "always-pass", description: "", capabilities: ["cap"], cost: 1 }];
    const report = runGoal(goal(), catalog, { "always-pass": alwaysPass });

    expect(report.outcome).toBe("done");
    expect(report.attempts).toHaveLength(1);
  });

  it("retries a failing cheap strategy before succeeding with a more capable one", () => {
    const catalog: Strategy[] = [
      { name: "always-fail", description: "", capabilities: ["cap"], cost: 1 },
      { name: "always-pass", description: "", capabilities: ["cap"], cost: 2 },
    ];
    const report = runGoal(goal(), catalog, { "always-fail": alwaysFail, "always-pass": alwaysPass });

    expect(report.outcome).toBe("done");
    expect(report.attempts).toHaveLength(2);
    expect(report.attempts[0]?.decision.kind).toBe("retry");
    expect(report.attempts[1]?.decision.kind).toBe("done");
  });

  it("escalates with attempts-exhausted when the budget runs out before success", () => {
    const catalog: Strategy[] = [
      { name: "always-fail", description: "", capabilities: ["cap"], cost: 1 },
      { name: "always-pass", description: "", capabilities: ["cap"], cost: 2 },
    ];
    const report = runGoal(goal({ maxAttempts: 1 }), catalog, { "always-fail": alwaysFail, "always-pass": alwaysPass });

    expect(report.outcome).toBe("escalated");
    expect(report.finalDecision.escalateCause).toBe("attempts-exhausted");
    expect(report.attempts).toHaveLength(1);
  });

  it("escalates with strategies-exhausted and records zero attempts when the plan is empty", () => {
    const catalog: Strategy[] = [{ name: "always-pass", description: "", capabilities: ["other-cap"], cost: 1 }];
    const report = runGoal(goal(), catalog, { "always-pass": alwaysPass });

    expect(report.outcome).toBe("escalated");
    expect(report.finalDecision.escalateCause).toBe("strategies-exhausted");
    expect(report.attempts).toHaveLength(0);
  });

  it("throws InvalidGoalSpecError before recording any attempts for a malformed goal", () => {
    const catalog: Strategy[] = [{ name: "always-pass", description: "", capabilities: ["cap"], cost: 1 }];
    expect(() => runGoal(goal({ id: "" }), catalog, { "always-pass": alwaysPass })).toThrow(InvalidGoalSpecError);
  });
});
