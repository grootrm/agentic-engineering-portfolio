import { describe, expect, it } from "vitest";
import { decide } from "../src/coding-agent-pipeline/critic.js";
import type { GoalSpec } from "../src/coding-agent-pipeline/goalSpec.js";
import type { PlanStep, Strategy } from "../src/coding-agent-pipeline/strategy.js";
import type { ValidationReport } from "../src/coding-agent-pipeline/validator.js";

function goal(maxAttempts: number): GoalSpec {
  return { id: "g", objective: "", targetFiles: [], scenario: null, acceptanceCriteria: [], constraints: [], maxAttempts };
}

function report(allPassed: boolean, failedIds: string[] = []): ValidationReport {
  return { attempt: 1, strategyName: "s", outcomes: [], allPassed, failedIds };
}

const strategyB: Strategy = { name: "b", description: "", capabilities: [], cost: 2 };
const stepB: PlanStep = { attempt: 2, strategy: strategyB, matchedCapabilities: [] };

describe("decide", () => {
  it("returns done when validation.allPassed", () => {
    const decision = decide(goal(3), [stepB], 1, report(true));
    expect(decision.kind).toBe("done");
  });

  it("returns retry with the next step's strategy name when attempts and steps remain", () => {
    const decision = decide(goal(3), [stepB], 1, report(false, ["x"]));
    expect(decision.kind).toBe("retry");
    expect(decision.nextStrategyName).toBe("b");
  });

  it("escalates with attempts-exhausted when the attempt budget is used up", () => {
    const decision = decide(goal(2), [stepB], 2, report(false, ["x"]));
    expect(decision.kind).toBe("escalate");
    expect(decision.escalateCause).toBe("attempts-exhausted");
  });

  it("escalates with strategies-exhausted when no steps remain, even with attempts left", () => {
    const decision = decide(goal(5), [], 1, report(false, ["x"]));
    expect(decision.kind).toBe("escalate");
    expect(decision.escalateCause).toBe("strategies-exhausted");
  });

  it("lists the failing check ids as diagnostics on escalate", () => {
    const decision = decide(goal(1), [], 1, report(false, ["check-a", "check-b"]));
    expect(decision.diagnostics).toEqual(["check-a", "check-b"]);
  });

  it("prioritizes attempts-exhausted over strategies-exhausted when both conditions hold", () => {
    const decision = decide(goal(1), [], 1, report(false, ["x"]));
    expect(decision.escalateCause).toBe("attempts-exhausted");
  });

  it("passes the current attempt number through on every decision kind", () => {
    expect(decide(goal(3), [stepB], 5, report(true)).attempt).toBe(5);
    expect(decide(goal(3), [stepB], 5, report(false, ["x"])).attempt).toBe(5);
  });
});
