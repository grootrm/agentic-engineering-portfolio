import { UnknownStrategyError } from "./errors.js";
import type { JsonObject } from "./jsonUtils.js";

export type StrategyFn<TInput, TOutput extends JsonObject = JsonObject> = (input: TInput) => TOutput;

export interface ExecutionResult<TOutput extends JsonObject = JsonObject> {
  readonly attempt: number;
  readonly strategyName: string;
  readonly output: TOutput | null;
  readonly thrownErrorName: string | null;
  readonly inputMutated: boolean;
}

/**
 * Looks up `strategyName` in `implementations` and runs it against `input`, in isolation:
 * a thrown error is captured into the result (name only) instead of propagating, and the
 * input is snapshotted before/after to detect accidental in-place mutation.
 */
export function executeStrategy<TInput, TOutput extends JsonObject = JsonObject>(
  attempt: number,
  strategyName: string,
  implementations: Record<string, StrategyFn<TInput, TOutput>>,
  input: TInput,
): ExecutionResult<TOutput> {
  const fn = implementations[strategyName];
  if (!fn) {
    throw new UnknownStrategyError(strategyName, Object.keys(implementations));
  }

  const beforeSnapshot = JSON.stringify(input);

  try {
    const output = fn(input);
    return {
      attempt,
      strategyName,
      output,
      thrownErrorName: null,
      inputMutated: beforeSnapshot !== JSON.stringify(input),
    };
  } catch (err) {
    return {
      attempt,
      strategyName,
      output: null,
      thrownErrorName: err instanceof Error ? err.name : "UnknownError",
      inputMutated: beforeSnapshot !== JSON.stringify(input),
    };
  }
}
