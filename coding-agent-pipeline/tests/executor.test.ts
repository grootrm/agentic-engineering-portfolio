import { describe, expect, it } from "vitest";
import { UnknownStrategyError } from "../src/coding-agent-pipeline/errors.js";
import { executeStrategy, type StrategyFn } from "../src/coding-agent-pipeline/executor.js";
import type { JsonObject } from "../src/coding-agent-pipeline/jsonUtils.js";

const double: StrategyFn<JsonObject, JsonObject> = (input) => ({ value: (input.value as number) * 2 });
const boom: StrategyFn<JsonObject, JsonObject> = () => {
  throw new RangeError("bad input");
};
const mutator: StrategyFn<JsonObject, JsonObject> = (input) => {
  (input as { value: number }).value = 999;
  return { value: 1 };
};

describe("executeStrategy", () => {
  it("applies the named strategy and returns its output", () => {
    const result = executeStrategy(1, "double", { double }, { value: 2 });
    expect(result.output).toEqual({ value: 4 });
    expect(result.thrownErrorName).toBeNull();
  });

  it("throws UnknownStrategyError for a strategy name not in the implementations map", () => {
    expect(() => executeStrategy(1, "missing", { double }, { value: 2 })).toThrow(UnknownStrategyError);
  });

  it("captures a thrown error as a result instead of propagating it", () => {
    const result = executeStrategy(1, "boom", { boom }, { value: 2 });
    expect(result.output).toBeNull();
    expect(result.thrownErrorName).toBe("RangeError");
  });

  it("detects when a strategy mutates its input in place", () => {
    const input = { value: 2 };
    const result = executeStrategy(1, "mutator", { mutator }, input);
    expect(result.inputMutated).toBe(true);
  });

  it("reports no mutation for a well-behaved strategy, and passes the attempt number through", () => {
    const input = { value: 2 };
    const result = executeStrategy(7, "double", { double }, input);
    expect(result.inputMutated).toBe(false);
    expect(result.attempt).toBe(7);
  });
});
