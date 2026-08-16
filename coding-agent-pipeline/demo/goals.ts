import type { AcceptanceCheck, Constraint, GoalSpec } from "../src/coding-agent-pipeline/goalSpec.js";
import type { JsonObject } from "../src/coding-agent-pipeline/jsonUtils.js";
import type { MergeScenarioInput } from "./mergeConfigTypes.js";

const LAYER_DEFAULTS: JsonObject = {
  server: { port: 8080, tags: ["default"] },
  featureFlags: { darkMode: true },
  limits: { maxUsers: 100 },
  secrets: { apiKey: "default-key-000" },
};

const LAYER_ENVIRONMENT: JsonObject = {
  server: { tags: ["staging"] },
  limits: { maxUsers: 250 },
};

const LAYER_USER_OVERRIDES: JsonObject = {
  server: { port: 9090, tags: ["prod", "default"] },
  featureFlags: { darkMode: null },
  limits: ["unlimited", "beta"],
};

const CONFIG_MERGE_SCENARIO: MergeScenarioInput = {
  layers: [LAYER_DEFAULTS, LAYER_ENVIRONMENT, LAYER_USER_OVERRIDES],
  policy: { arrays: "concat-dedupe", nullMeansDelete: true, onTypeConflict: "override" },
};

const CONFIG_MERGE_ACCEPTANCE_CRITERIA: AcceptanceCheck[] = [
  {
    id: "server-port",
    description: "The highest-precedence layer's server.port wins.",
    requiredCapability: "recursive",
    kind: "path-equals",
    path: ["server", "port"],
    expected: 9090,
  },
  {
    id: "server-tags",
    description: "server.tags is concat-deduped across all three layers, in layer order.",
    requiredCapability: "array-policy",
    kind: "path-equals",
    path: ["server", "tags"],
    expected: ["default", "staging", "prod"],
  },
  {
    id: "dark-mode-deleted",
    description: "A null override deletes featureFlags.darkMode instead of overwriting it with null.",
    requiredCapability: "null-delete",
    kind: "path-absent",
    path: ["featureFlags", "darkMode"],
  },
  {
    id: "limits-type",
    description: "An object/array type collision at `limits` is replaced wholesale, not merged key-wise.",
    requiredCapability: "type-conflict",
    kind: "path-type",
    path: ["limits"],
    expectedType: "array",
  },
];

const CONFIG_MERGE_CONSTRAINTS: Constraint[] = [
  {
    id: "no-input-mutation",
    description: "mergeConfig must not mutate the layers it was given.",
    kind: "forbid-input-mutation",
  },
  {
    id: "secret-immutable",
    description: "secrets.apiKey is never touched by later layers and must survive the merge unchanged.",
    kind: "protected-path-immutable",
    path: ["secrets", "apiKey"],
    expected: "default-key-000",
  },
  {
    id: "depth-bound",
    description: "The merged config must not exceed a sane nesting depth.",
    kind: "max-output-depth",
    maxDepth: 6,
  },
];

/** Retries through all four strategies, succeeding on attempt 4 (full-featured-merge). */
export const HAPPY_PATH_GOAL: GoalSpec<MergeScenarioInput> = {
  id: "config-merge-happy-path",
  objective: "Merge three layered config objects (defaults -> environment -> user overrides) into one.",
  targetFiles: ["config/mergeConfig.ts"],
  scenario: CONFIG_MERGE_SCENARIO,
  acceptanceCriteria: CONFIG_MERGE_ACCEPTANCE_CRITERIA,
  constraints: CONFIG_MERGE_CONSTRAINTS,
  maxAttempts: 4,
};

/** Same scenario, tighter attempt budget: exhausts its budget with 2 checks still failing. */
export const ESCALATE_GOAL: GoalSpec<MergeScenarioInput> = {
  ...HAPPY_PATH_GOAL,
  id: "config-merge-escalate",
  maxAttempts: 2,
};

/** No strategy declares the required capability, so the plan is empty and it escalates immediately. */
export const IMPOSSIBLE_GOAL: GoalSpec<MergeScenarioInput> = {
  id: "config-merge-impossible",
  objective: "Merge config layers using a capability no strategy in the catalog implements.",
  targetFiles: ["config/mergeConfig.ts"],
  scenario: { layers: [LAYER_DEFAULTS], policy: CONFIG_MERGE_SCENARIO.policy },
  acceptanceCriteria: [
    {
      id: "quantum-merge-check",
      description: "Requires a capability that does not exist in the strategy catalog.",
      requiredCapability: "quantum-merge",
      kind: "path-equals",
      path: ["server", "port"],
      expected: 9090,
    },
  ],
  constraints: [],
  maxAttempts: 3,
};

/** Simple enough that the cheapest strategy (recursive-merge) satisfies it on the first attempt. */
export const MINIMAL_GOAL: GoalSpec<MergeScenarioInput> = {
  id: "config-merge-minimal",
  objective: "Merge two config layers where only nested-object merging is required.",
  targetFiles: ["config/mergeConfig.ts"],
  scenario: {
    layers: [{ app: { name: "demo" } }, { app: { version: "1.0" } }],
    policy: { arrays: "replace", nullMeansDelete: false, onTypeConflict: "override" },
  },
  acceptanceCriteria: [
    {
      id: "app-name",
      description: "The un-overridden app.name survives a nested merge.",
      requiredCapability: "recursive",
      kind: "path-equals",
      path: ["app", "name"],
      expected: "demo",
    },
  ],
  constraints: [],
  maxAttempts: 3,
};

export type DemoGoalName = "minimal" | "happy-path" | "escalate" | "impossible";

const DEMO_GOALS: Record<DemoGoalName, GoalSpec<MergeScenarioInput>> = {
  minimal: MINIMAL_GOAL,
  "happy-path": HAPPY_PATH_GOAL,
  escalate: ESCALATE_GOAL,
  impossible: IMPOSSIBLE_GOAL,
};

export function selectDemoGoal(name: string, maxAttemptsOverride?: number): GoalSpec<MergeScenarioInput> {
  const goal = DEMO_GOALS[name as DemoGoalName];
  if (!goal) {
    throw new Error(`Unknown demo goal "${name}" (known: ${Object.keys(DEMO_GOALS).join(", ")})`);
  }
  if (maxAttemptsOverride === undefined) return goal;
  return { ...goal, maxAttempts: maxAttemptsOverride };
}
