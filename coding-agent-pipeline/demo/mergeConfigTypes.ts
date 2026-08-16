import type { JsonObject } from "../src/coding-agent-pipeline/jsonUtils.js";

export type ArrayPolicy = "replace" | "concat" | "concat-dedupe";
export type TypeConflictPolicy = "override" | "error";

export interface MergePolicy {
  readonly arrays: ArrayPolicy;
  readonly nullMeansDelete: boolean;
  readonly onTypeConflict: TypeConflictPolicy;
}

/** The scenario payload a mergeConfig strategy runs against. */
export interface MergeScenarioInput {
  readonly layers: JsonObject[];
  readonly policy: MergePolicy;
}

export type MergeCapability = "recursive" | "array-policy" | "null-delete" | "type-conflict";
