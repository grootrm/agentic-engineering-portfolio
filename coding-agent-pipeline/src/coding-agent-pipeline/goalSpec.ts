import type { JsonType, JsonValue } from "./jsonUtils.js";

/**
 * Pure data. No behavior lives here — evaluation logic lives in validator.ts.
 * The minimum input to the pipeline: a fully-specified coding task.
 */
export interface GoalSpec<TInput = unknown> {
  readonly id: string;
  readonly objective: string;
  /** Symbolic file identifiers this goal is scoped to (not real fs paths in the demo). */
  readonly targetFiles: string[];
  /** Domain payload the Executor's chosen strategy is run against. */
  readonly scenario: TInput;
  readonly acceptanceCriteria: AcceptanceCheck[];
  readonly constraints: Constraint[];
  readonly maxAttempts: number;
}

export type AcceptanceCheckKind = "path-equals" | "path-absent" | "path-type" | "throws" | "no-throws";

export interface AcceptanceCheck {
  readonly id: string;
  readonly description: string;
  /** Capability tag the Planner uses to decide which strategies are even relevant. */
  readonly requiredCapability: string;
  readonly kind: AcceptanceCheckKind;
  readonly path?: string[];
  readonly expected?: JsonValue; // path-equals
  readonly expectedType?: JsonType; // path-type
  readonly expectedErrorName?: string; // throws
}

export type ConstraintKind = "forbid-input-mutation" | "protected-path-immutable" | "max-output-depth";

export interface Constraint {
  readonly id: string;
  readonly description: string;
  readonly kind: ConstraintKind;
  readonly path?: string[]; // protected-path-immutable
  readonly expected?: JsonValue; // protected-path-immutable
  readonly maxDepth?: number; // max-output-depth
}
