import { describe, expect, it } from "vitest";
import {
  fullFeaturedMerge,
  recursiveMerge,
  recursiveMergeWithArrays,
  recursiveMergeWithNullDelete,
  TypeConflictError,
} from "../demo/mergeConfigStrategies.js";
import type { MergePolicy } from "../demo/mergeConfigTypes.js";
import type { JsonObject } from "../src/coding-agent-pipeline/jsonUtils.js";

const REPLACE_POLICY: MergePolicy = { arrays: "replace", nullMeansDelete: false, onTypeConflict: "override" };
const CONCAT_DEDUPE_POLICY: MergePolicy = { arrays: "concat-dedupe", nullMeansDelete: true, onTypeConflict: "override" };

describe("recursiveMerge (level 1)", () => {
  it("recursively merges nested object siblings from both layers", () => {
    const layers: JsonObject[] = [{ a: { x: 1, y: 2 } }, { a: { y: 3 } }];
    const result = recursiveMerge({ layers, policy: REPLACE_POLICY });
    expect(result).toEqual({ a: { x: 1, y: 3 } });
  });

  it("always replaces arrays wholesale, ignoring policy.arrays", () => {
    const layers: JsonObject[] = [{ tags: ["a", "b"] }, { tags: ["c"] }];
    const result = recursiveMerge({ layers, policy: CONCAT_DEDUPE_POLICY });
    expect(result).toEqual({ tags: ["c"] });
  });

  it("overwrites with a literal null instead of deleting the key", () => {
    const layers: JsonObject[] = [{ flag: true }, { flag: null }];
    const result = recursiveMerge({ layers, policy: CONCAT_DEDUPE_POLICY });
    expect(result).toEqual({ flag: null });
    expect("flag" in result).toBe(true);
  });

  it("corrupts an object/array type collision instead of replacing it wholesale", () => {
    const layers: JsonObject[] = [{ limits: { maxUsers: 5 } }, { limits: ["unlimited"] }];
    const result = recursiveMerge({ layers, policy: REPLACE_POLICY });
    expect(Array.isArray(result.limits)).toBe(false);
    expect(result.limits).not.toEqual(["unlimited"]);
  });
});

describe("recursiveMergeWithArrays (level 2)", () => {
  it("concat-dedupes arrays when the policy asks for it", () => {
    const layers: JsonObject[] = [{ tags: ["a", "b"] }, { tags: ["b", "c"] }];
    const result = recursiveMergeWithArrays({ layers, policy: CONCAT_DEDUPE_POLICY });
    expect(result).toEqual({ tags: ["a", "b", "c"] });
  });
});

describe("recursiveMergeWithNullDelete (level 3)", () => {
  it("deletes the key when the value is null and the policy says so", () => {
    const layers: JsonObject[] = [{ flag: true }, { flag: null }];
    const result = recursiveMergeWithNullDelete({ layers, policy: CONCAT_DEDUPE_POLICY });
    expect(result).toEqual({});
    expect("flag" in result).toBe(false);
  });
});

describe("fullFeaturedMerge (level 4)", () => {
  it("replaces a type collision wholesale under onTypeConflict: override", () => {
    const layers: JsonObject[] = [{ limits: { maxUsers: 5 } }, { limits: ["unlimited"] }];
    const result = fullFeaturedMerge({ layers, policy: CONCAT_DEDUPE_POLICY });
    expect(result).toEqual({ limits: ["unlimited"] });
  });

  it("throws TypeConflictError under onTypeConflict: error", () => {
    const layers: JsonObject[] = [{ limits: { maxUsers: 5 } }, { limits: ["unlimited"] }];
    const errorPolicy: MergePolicy = { ...CONCAT_DEDUPE_POLICY, onTypeConflict: "error" };
    expect(() => fullFeaturedMerge({ layers, policy: errorPolicy })).toThrow(TypeConflictError);
  });
});
