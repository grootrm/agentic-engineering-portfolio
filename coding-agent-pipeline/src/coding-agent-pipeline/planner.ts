import type { GoalSpec } from "./goalSpec.js";
import type { Plan, PlanStep, Strategy } from "./strategy.js";

/**
 * Filters `catalog` down to strategies relevant to the goal's declared acceptance criteria
 * (at least one matching capability, or every strategy if the goal requires none), then
 * orders survivors cheapest-first — try the simplest plausible fix before a bigger rewrite.
 * Ties are broken by strategy name for a stable, deterministic order.
 */
export function planStrategies(goal: GoalSpec, catalog: Strategy[]): Plan {
  const requiredCapabilities = new Set(goal.acceptanceCriteria.map((c) => c.requiredCapability));

  const relevant = catalog.filter((strategy) => {
    if (requiredCapabilities.size === 0) return true;
    return strategy.capabilities.some((capability) => requiredCapabilities.has(capability));
  });

  const sorted = [...relevant].sort((a, b) => a.cost - b.cost || a.name.localeCompare(b.name));

  const steps: PlanStep[] = sorted.map((strategy, index) => ({
    attempt: index + 1,
    strategy,
    matchedCapabilities: strategy.capabilities.filter((capability) => requiredCapabilities.has(capability)),
  }));

  return { goalId: goal.id, steps };
}
