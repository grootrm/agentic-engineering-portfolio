import { describe, expect, it } from "vitest";
import { deepCloneJson, deepEqualJson, depthOfJson, getAtPath, typeOfJson } from "../src/coding-agent-pipeline/jsonUtils.js";

describe("deepCloneJson", () => {
  it("produces a value that does not share array/object references with the original", () => {
    const original = { a: [1, { b: 2 }] };
    const clone = deepCloneJson(original);

    expect(clone).toEqual(original);
    expect(clone).not.toBe(original);
    expect(clone.a).not.toBe(original.a);
    expect(clone.a[1]).not.toBe(original.a[1]);
  });
});

describe("deepEqualJson", () => {
  it("treats an array and an object with equivalent-looking entries as unequal", () => {
    expect(deepEqualJson([1, 2], { "0": 1, "1": 2 })).toBe(false);
  });

  it("compares nested structures by value regardless of key order", () => {
    expect(deepEqualJson({ a: 1, b: [1, 2] }, { b: [1, 2], a: 1 })).toBe(true);
  });
});

describe("getAtPath", () => {
  it("walks through nested objects and arrays", () => {
    const value = { a: { b: [10, 20, { c: "found" }] } };
    expect(getAtPath(value, ["a", "b", "2", "c"])).toBe("found");
  });

  it("returns undefined for a missing path", () => {
    const value = { a: { b: 1 } };
    expect(getAtPath(value, ["a", "missing", "x"])).toBeUndefined();
  });
});

describe("typeOfJson", () => {
  it("discriminates array, object, null, and primitives", () => {
    expect(typeOfJson([])).toBe("array");
    expect(typeOfJson({})).toBe("object");
    expect(typeOfJson(null)).toBe("null");
    expect(typeOfJson("x")).toBe("string");
    expect(typeOfJson(1)).toBe("number");
    expect(typeOfJson(true)).toBe("boolean");
  });
});

describe("depthOfJson", () => {
  it("measures nesting depth, with an empty object/array counting as depth 1", () => {
    expect(depthOfJson("x")).toBe(0);
    expect(depthOfJson({})).toBe(1);
    expect(depthOfJson({ a: { b: { c: 1 } } })).toBe(3);
    expect(depthOfJson({ a: [1, [2, 3]] })).toBe(3);
  });
});
