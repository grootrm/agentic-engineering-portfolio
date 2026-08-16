import { describe, expect, it } from "vitest";
import type { GoalSpec } from "../src/coding-agent-pipeline/goalSpec.js";
import { planStrategies } from "../src/coding-agent-pipeline/planner.js";
import type { Strategy } from "../src/coding-agent-pipeline/strategy.js";

const CATALOG: Strategy[] = [
  { name: "cheap-a", description: "", capabilities: ["a"], cost: 1 },
  { name: "cheap-b", description: "", capabilities: ["b"], cost: 1 },
  { name: "mid-ab", description: "", capabilities: ["a", "b"], cost: 2 },
  { name: "expensive-ab", description: "", capabilities: ["a", "b", "c"], cost: 4 },
];

function goalRequiring(capabilities: string[]): GoalSpec {
  return {
    id: "g",
    objective: "",
    targetFiles: [],
    scenario: null,
    acceptanceCriteria: capabilities.map((cap, i) => ({
      id: `check-${i}`,
      description: "",
      requiredCapability: cap,
      kind: "no-throws" as const,
    })),
    constraints: [],
    maxAttempts: 5,
  };
}

describe("planStrategies", () => {
  it("orders every matching strategy cheapest-first when both capabilities are required", () => {
    const plan = planStrategies(goalRequiring(["a", "b"]), CATALOG);
    expect(plan.steps.map((s) => s.strategy.name)).toEqual(["cheap-a", "cheap-b", "mid-ab", "expensive-ab"]);
    expect(plan.steps.map((s) => s.attempt)).toEqual([1, 2, 3, 4]);
  });

  it("filters out strategies with no relevant capability when a narrow capability is required", () => {
    const plan = planStrategies(goalRequiring(["c"]), CATALOG);
    expect(plan.steps.map((s) => s.strategy.name)).toEqual(["expensive-ab"]);
  });

  it("includes the full catalog, cost-ordered, when the goal requires no capabilities", () => {
    const plan = planStrategies(goalRequiring([]), CATALOG);
    expect(plan.steps.map((s) => s.strategy.name)).toEqual(["cheap-a", "cheap-b", "mid-ab", "expensive-ab"]);
  });

  it("produces an empty plan when no strategy declares the required capability", () => {
    const plan = planStrategies(goalRequiring(["nonexistent"]), CATALOG);
    expect(plan.steps).toEqual([]);
  });

  it("breaks a cost tie by strategy name", () => {
    const tiedCatalog: Strategy[] = [
      { name: "zeta", description: "", capabilities: ["x"], cost: 1 },
      { name: "alpha", description: "", capabilities: ["x"], cost: 1 },
    ];
    const plan = planStrategies(goalRequiring(["x"]), tiedCatalog);
    expect(plan.steps.map((s) => s.strategy.name)).toEqual(["alpha", "zeta"]);
  });
});
