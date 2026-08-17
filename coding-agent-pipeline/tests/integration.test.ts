import { describe, expect, it } from "vitest";
import { ESCALATE_GOAL, HAPPY_PATH_GOAL, IMPOSSIBLE_GOAL, MINIMAL_GOAL } from "../demo/goals.js";
import { STRATEGY_CATALOG, STRATEGY_IMPLEMENTATIONS } from "../demo/mergeConfigStrategies.js";
import { runGoal } from "../src/coding-agent-pipeline/orchestrator.js";

describe("full pipeline — happy path", () => {
  it("retries through all four strategies, reaching done on attempt 4 via full-featured-merge", () => {
    const report = runGoal(HAPPY_PATH_GOAL, STRATEGY_CATALOG, STRATEGY_IMPLEMENTATIONS);

    expect(report.outcome).toBe("done");
    expect(report.attempts).toHaveLength(4);
    expect(report.attempts.map((a) => a.strategy.name)).toEqual([
      "recursive-merge",
      "recursive-merge-with-arrays",
      "recursive-merge-with-null-delete",
      "full-featured-merge",
    ]);
  });

  it("fails a strictly shrinking, specific set of checks on attempts 1 through 3", () => {
    const report = runGoal(HAPPY_PATH_GOAL, STRATEGY_CATALOG, STRATEGY_IMPLEMENTATIONS);

    expect(report.attempts[0]?.validation.failedIds.sort()).toEqual(["dark-mode-deleted", "limits-type", "server-tags"].sort());
    expect(report.attempts[1]?.validation.failedIds.sort()).toEqual(["dark-mode-deleted", "limits-type"].sort());
    expect(report.attempts[2]?.validation.failedIds).toEqual(["limits-type"]);
    expect(report.attempts[3]?.validation.allPassed).toBe(true);
  });

  it("keeps the baseline constraints (no mutation, protected secret) passing on every attempt", () => {
    const report = runGoal(HAPPY_PATH_GOAL, STRATEGY_CATALOG, STRATEGY_IMPLEMENTATIONS);

    for (const attempt of report.attempts) {
      const noMutation = attempt.validation.outcomes.find((o) => o.id === "no-input-mutation");
      const secretImmutable = attempt.validation.outcomes.find((o) => o.id === "secret-immutable");
      expect(noMutation?.passed).toBe(true);
      expect(secretImmutable?.passed).toBe(true);
    }
  });
});

describe("full pipeline — escalation", () => {
  it("escalates with attempts-exhausted after a 2-attempt budget, diagnostics listing what's still failing", () => {
    const report = runGoal(ESCALATE_GOAL, STRATEGY_CATALOG, STRATEGY_IMPLEMENTATIONS);

    expect(report.outcome).toBe("escalated");
    expect(report.finalDecision.escalateCause).toBe("attempts-exhausted");
    expect(report.attempts).toHaveLength(2);
    expect(report.finalDecision.diagnostics?.sort()).toEqual(["dark-mode-deleted", "limits-type"].sort());
  });

  it("escalates with strategies-exhausted and zero attempts when no strategy matches the goal", () => {
    const report = runGoal(IMPOSSIBLE_GOAL, STRATEGY_CATALOG, STRATEGY_IMPLEMENTATIONS);

    expect(report.outcome).toBe("escalated");
    expect(report.finalDecision.escalateCause).toBe("strategies-exhausted");
    expect(report.attempts).toHaveLength(0);
  });
});

describe("full pipeline — minimal goal", () => {
  it("reaches done on attempt 1 using the cheapest strategy", () => {
    const report = runGoal(MINIMAL_GOAL, STRATEGY_CATALOG, STRATEGY_IMPLEMENTATIONS);

    expect(report.outcome).toBe("done");
    expect(report.attempts).toHaveLength(1);
    expect(report.attempts[0]?.strategy.name).toBe("recursive-merge");
  });
});
