import type { StrategyFn } from "../src/coding-agent-pipeline/executor.js";
import { deepCloneJson, deepEqualJson, type JsonObject, type JsonValue } from "../src/coding-agent-pipeline/jsonUtils.js";
import type { Strategy } from "../src/coding-agent-pipeline/strategy.js";
import type { MergeCapability, MergePolicy, MergeScenarioInput } from "./mergeConfigTypes.js";

export class TypeConflictError extends Error {
  readonly key: string;
  readonly targetType: string;
  readonly sourceType: string;

  constructor(key: string, targetType: string, sourceType: string) {
    super(`Type conflict at "${key}": target is ${targetType}, source is ${sourceType}`);
    this.name = "TypeConflictError";
    this.key = key;
    this.targetType = targetType;
    this.sourceType = sourceType;
  }
}

function isPlainObject(value: JsonValue): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** Converts an array (or object) to a plain key/value map so the naive merge branch can walk it uniformly. */
function asEntriesObject(value: JsonObject | JsonValue[]): JsonObject {
  if (Array.isArray(value)) {
    return Object.fromEntries(value.map((item, index) => [String(index), item]));
  }
  return value;
}

function dedupeConcat(a: JsonValue[], b: JsonValue[]): JsonValue[] {
  const merged = [...a, ...b];
  const deduped: JsonValue[] = [];
  for (const item of merged) {
    if (!deduped.some((existing) => deepEqualJson(existing, item))) deduped.push(item);
  }
  return deduped;
}

function mergeTwo(target: JsonObject, source: JsonObject, policy: MergePolicy, capabilities: Set<MergeCapability>): JsonObject {
  const result: JsonObject = { ...target };

  for (const key of Object.keys(source)) {
    const s = source[key] ?? null;
    const t = key in target ? (target[key] ?? null) : undefined;

    if (s === null) {
      if (capabilities.has("null-delete") && policy.nullMeansDelete) {
        delete result[key];
      } else {
        result[key] = null;
      }
      continue;
    }

    const tIsArray = Array.isArray(t);
    const sIsArray = Array.isArray(s);
    const tIsObject = isPlainObject(t ?? null);
    const sIsObject = isPlainObject(s);

    const isTypeCollision = t !== undefined && t !== null && ((tIsArray && sIsObject) || (tIsObject && sIsArray));

    if (isTypeCollision) {
      if (capabilities.has("type-conflict")) {
        if (policy.onTypeConflict === "error") {
          throw new TypeConflictError(key, tIsArray ? "array" : "object", sIsArray ? "array" : "object");
        }
        result[key] = deepCloneJson(s);
      } else {
        // Naive bug: a check that only asks "is this an object?" (without excluding arrays)
        // treats an object/array type collision as mergeable, corrupting the result instead
        // of replacing it wholesale.
        result[key] = mergeTwo(asEntriesObject(t as JsonObject | JsonValue[]), asEntriesObject(s), policy, capabilities);
      }
      continue;
    }

    if (sIsArray) {
      if (!capabilities.has("array-policy") || !tIsArray) {
        result[key] = deepCloneJson(s);
      } else if (policy.arrays === "replace") {
        result[key] = deepCloneJson(s);
      } else if (policy.arrays === "concat") {
        result[key] = [...(t as JsonValue[]), ...s];
      } else {
        result[key] = dedupeConcat(t as JsonValue[], s);
      }
      continue;
    }

    if (sIsObject && tIsObject) {
      result[key] = mergeTwo(t as JsonObject, s, policy, capabilities);
      continue;
    }

    result[key] = deepCloneJson(s);
  }

  return result;
}

function mergeCore(layers: JsonObject[], policy: MergePolicy, capabilities: Set<MergeCapability>): JsonObject {
  let result: JsonObject = {};
  for (const layer of layers) {
    result = mergeTwo(result, layer, policy, capabilities);
  }
  return result;
}

function makeStrategy(capabilities: MergeCapability[]): StrategyFn<MergeScenarioInput, JsonObject> {
  const capabilitySet = new Set(capabilities);
  return (input: MergeScenarioInput): JsonObject => mergeCore(input.layers, input.policy, capabilitySet);
}

export const recursiveMerge = makeStrategy(["recursive"]);
export const recursiveMergeWithArrays = makeStrategy(["recursive", "array-policy"]);
export const recursiveMergeWithNullDelete = makeStrategy(["recursive", "array-policy", "null-delete"]);
export const fullFeaturedMerge = makeStrategy(["recursive", "array-policy", "null-delete", "type-conflict"]);

export const STRATEGY_CATALOG: Strategy[] = [
  {
    name: "recursive-merge",
    description: "Recursively merges nested objects. Arrays are always replaced wholesale; null overwrites rather than deletes; an object/array type collision is merged key-wise instead of replaced.",
    capabilities: ["recursive"],
    cost: 1,
  },
  {
    name: "recursive-merge-with-arrays",
    description: "Adds policy.arrays support (replace / concat / concat-dedupe) for array-vs-array merges.",
    capabilities: ["recursive", "array-policy"],
    cost: 2,
  },
  {
    name: "recursive-merge-with-null-delete",
    description: "Adds policy.nullMeansDelete support: a null value deletes the key instead of overwriting it.",
    capabilities: ["recursive", "array-policy", "null-delete"],
    cost: 3,
  },
  {
    name: "full-featured-merge",
    description: "Adds correct object/array type-conflict handling: wholesale replace under \"override\", or a thrown TypeConflictError under \"error\".",
    capabilities: ["recursive", "array-policy", "null-delete", "type-conflict"],
    cost: 4,
  },
];

export const STRATEGY_IMPLEMENTATIONS: Record<string, StrategyFn<MergeScenarioInput, JsonObject>> = {
  "recursive-merge": recursiveMerge,
  "recursive-merge-with-arrays": recursiveMergeWithArrays,
  "recursive-merge-with-null-delete": recursiveMergeWithNullDelete,
  "full-featured-merge": fullFeaturedMerge,
};
