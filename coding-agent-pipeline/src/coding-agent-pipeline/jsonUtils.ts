/** JSON-value types and small structural helpers shared by the core engine and the demo domain. */

export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
export type JsonObject = { [key: string]: JsonValue };
export type JsonType = "object" | "array" | "string" | "number" | "boolean" | "null";

export function typeOfJson(value: JsonValue): JsonType {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  return typeof value as "object" | "string" | "number" | "boolean";
}

export function deepCloneJson<T extends JsonValue>(value: T): T {
  if (value === null || typeof value !== "object") return value;
  if (Array.isArray(value)) {
    return value.map((item) => deepCloneJson(item)) as unknown as T;
  }
  const out: JsonObject = {};
  for (const [key, val] of Object.entries(value as JsonObject)) {
    out[key] = deepCloneJson(val);
  }
  return out as unknown as T;
}

export function deepEqualJson(a: JsonValue, b: JsonValue): boolean {
  if (a === b) return true;
  const aType = typeOfJson(a);
  const bType = typeOfJson(b);
  if (aType !== bType) return false;

  if (aType === "array") {
    const aArr = a as JsonValue[];
    const bArr = b as JsonValue[];
    if (aArr.length !== bArr.length) return false;
    return aArr.every((item, i) => deepEqualJson(item, bArr[i] ?? null));
  }

  if (aType === "object") {
    const aObj = a as JsonObject;
    const bObj = b as JsonObject;
    const aKeys = Object.keys(aObj).sort();
    const bKeys = Object.keys(bObj).sort();
    if (aKeys.length !== bKeys.length) return false;
    return aKeys.every((key, i) => key === bKeys[i] && deepEqualJson(aObj[key] ?? null, bObj[key] ?? null));
  }

  return false;
}

/** Walks `path` through nested objects/arrays. Returns `undefined` if any segment is missing. */
export function getAtPath(value: JsonValue, path: string[]): JsonValue | undefined {
  let current: JsonValue | undefined = value;
  for (const segment of path) {
    if (current === null || current === undefined || typeof current !== "object") return undefined;
    if (Array.isArray(current)) {
      const index = Number(segment);
      if (!Number.isInteger(index)) return undefined;
      current = current[index];
    } else {
      current = (current as JsonObject)[segment];
    }
  }
  return current;
}

export function hasAtPath(value: JsonValue, path: string[]): boolean {
  return getAtPath(value, path) !== undefined;
}

export function depthOfJson(value: JsonValue): number {
  if (value === null || typeof value !== "object") return 0;
  const entries = Array.isArray(value) ? value : Object.values(value);
  if (entries.length === 0) return 1;
  return 1 + Math.max(...entries.map((item) => depthOfJson(item)));
}
