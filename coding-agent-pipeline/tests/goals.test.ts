import { describe, expect, it } from "vitest";
import { ESCALATE_GOAL, HAPPY_PATH_GOAL, IMPOSSIBLE_GOAL, MINIMAL_GOAL, selectDemoGoal } from "../demo/goals.js";

describe("selectDemoGoal", () => {
  it("resolves each known name to the matching goal", () => {
    expect(selectDemoGoal("minimal").id).toBe(MINIMAL_GOAL.id);
    expect(selectDemoGoal("happy-path").id).toBe(HAPPY_PATH_GOAL.id);
    expect(selectDemoGoal("escalate").id).toBe(ESCALATE_GOAL.id);
    expect(selectDemoGoal("impossible").id).toBe(IMPOSSIBLE_GOAL.id);
  });

  it("throws a clear error for an unknown goal name", () => {
    expect(() => selectDemoGoal("nonexistent")).toThrow(/Unknown demo goal/);
  });

  it("overrides maxAttempts when provided, leaving everything else unchanged", () => {
    const goal = selectDemoGoal("happy-path", 10);
    expect(goal.maxAttempts).toBe(10);
    expect(goal.id).toBe(HAPPY_PATH_GOAL.id);
    expect(goal.scenario).toEqual(HAPPY_PATH_GOAL.scenario);
  });
});
