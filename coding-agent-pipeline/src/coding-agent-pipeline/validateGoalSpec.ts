import { InvalidGoalSpecError } from "./errors.js";
import type { GoalSpec } from "./goalSpec.js";

/** Throws InvalidGoalSpecError (with every violation collected into `reasons`) if the goal is malformed. */
export function validateGoalSpec(goal: GoalSpec): void {
  const reasons: string[] = [];

  if (goal.id.trim().length === 0) reasons.push("id must not be empty");
  if (goal.objective.trim().length === 0) reasons.push("objective must not be empty");
  if (!Number.isInteger(goal.maxAttempts) || goal.maxAttempts <= 0) {
    reasons.push("maxAttempts must be a positive integer");
  }

  const acceptanceIds = goal.acceptanceCriteria.map((c) => c.id);
  const duplicateAcceptanceIds = findDuplicates(acceptanceIds);
  if (duplicateAcceptanceIds.length > 0) {
    reasons.push(`duplicate acceptanceCriteria ids: ${duplicateAcceptanceIds.join(", ")}`);
  }

  const constraintIds = goal.constraints.map((c) => c.id);
  const duplicateConstraintIds = findDuplicates(constraintIds);
  if (duplicateConstraintIds.length > 0) {
    reasons.push(`duplicate constraint ids: ${duplicateConstraintIds.join(", ")}`);
  }

  if (reasons.length > 0) {
    throw new InvalidGoalSpecError(goal.id, reasons);
  }
}

function findDuplicates(values: string[]): string[] {
  const seen = new Set<string>();
  const duplicates = new Set<string>();
  for (const value of values) {
    if (seen.has(value)) duplicates.add(value);
    seen.add(value);
  }
  return [...duplicates];
}
