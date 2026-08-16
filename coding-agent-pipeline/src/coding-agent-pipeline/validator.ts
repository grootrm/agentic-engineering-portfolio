import type { ExecutionResult } from "./executor.js";
import type { AcceptanceCheck, Constraint, GoalSpec } from "./goalSpec.js";
import { deepEqualJson, depthOfJson, getAtPath, hasAtPath, typeOfJson, type JsonObject } from "./jsonUtils.js";

export interface CheckOutcome {
  readonly id: string;
  readonly kind: "acceptance" | "constraint";
  readonly passed: boolean;
  readonly detail: string;
}

export interface ValidationReport {
  readonly attempt: number;
  readonly strategyName: string;
  readonly outcomes: CheckOutcome[];
  readonly allPassed: boolean;
  readonly failedIds: string[];
}

/** Scores an execution against the goal's acceptanceCriteria and constraints. */
export function validate(goal: GoalSpec, execution: ExecutionResult): ValidationReport {
  const outcomes: CheckOutcome[] = [
    ...goal.acceptanceCriteria.map((check) => evaluateAcceptanceCheck(check, execution)),
    ...goal.constraints.map((constraint) => evaluateConstraint(constraint, execution)),
  ];

  const failedIds = outcomes.filter((o) => !o.passed).map((o) => o.id);

  return {
    attempt: execution.attempt,
    strategyName: execution.strategyName,
    outcomes,
    allPassed: failedIds.length === 0,
    failedIds,
  };
}

function evaluateAcceptanceCheck(check: AcceptanceCheck, execution: ExecutionResult): CheckOutcome {
  if (check.kind === "throws") {
    const passed =
      execution.thrownErrorName !== null &&
      (check.expectedErrorName === undefined || execution.thrownErrorName === check.expectedErrorName);
    return outcome(check.id, "acceptance", passed, `expected throw${check.expectedErrorName ? ` "${check.expectedErrorName}"` : ""}, got ${execution.thrownErrorName ?? "no throw"}`);
  }

  if (check.kind === "no-throws") {
    const passed = execution.thrownErrorName === null;
    return outcome(check.id, "acceptance", passed, passed ? "did not throw" : `threw "${execution.thrownErrorName}"`);
  }

  if (execution.output === null) {
    return outcome(check.id, "acceptance", false, "no output (execution threw)");
  }

  const path = check.path ?? [];
  const value = getAtPath(execution.output, path) ?? null;

  if (check.kind === "path-equals") {
    const passed = deepEqualJson(value, check.expected ?? null);
    return outcome(check.id, "acceptance", passed, `at [${path.join(".")}]: expected ${JSON.stringify(check.expected)}, got ${JSON.stringify(value)}`);
  }

  if (check.kind === "path-absent") {
    const passed = !hasAtPath(execution.output, path);
    return outcome(check.id, "acceptance", passed, passed ? `[${path.join(".")}] absent as expected` : `[${path.join(".")}] unexpectedly present`);
  }

  // path-type
  const actualType = typeOfJson(value);
  const passed = actualType === check.expectedType;
  return outcome(check.id, "acceptance", passed, `at [${path.join(".")}]: expected type ${check.expectedType}, got ${actualType}`);
}

function evaluateConstraint(constraint: Constraint, execution: ExecutionResult): CheckOutcome {
  if (constraint.kind === "forbid-input-mutation") {
    const passed = !execution.inputMutated;
    return outcome(constraint.id, "constraint", passed, passed ? "input left unmodified" : "input was mutated");
  }

  if (execution.output === null) {
    return outcome(constraint.id, "constraint", false, "no output (execution threw)");
  }

  if (constraint.kind === "protected-path-immutable") {
    const path = constraint.path ?? [];
    const value = getAtPath(execution.output, path) ?? null;
    const passed = deepEqualJson(value, constraint.expected ?? null);
    return outcome(constraint.id, "constraint", passed, `protected [${path.join(".")}]: expected ${JSON.stringify(constraint.expected)}, got ${JSON.stringify(value)}`);
  }

  // max-output-depth
  const depth = depthOfJson(execution.output as unknown as JsonObject);
  const passed = constraint.maxDepth !== undefined && depth <= constraint.maxDepth;
  return outcome(constraint.id, "constraint", passed, `output depth ${depth}, max allowed ${constraint.maxDepth}`);
}

function outcome(id: string, kind: "acceptance" | "constraint", passed: boolean, detail: string): CheckOutcome {
  return { id, kind, passed, detail };
}
