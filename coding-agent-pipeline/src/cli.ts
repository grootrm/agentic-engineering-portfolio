#!/usr/bin/env node
/**
 * Runs the coding-agent-pipeline demo end to end.
 *
 * Examples:
 *   npm run demo -- --goal minimal
 *   npm run demo -- --goal happy-path
 *   npm run demo -- --goal escalate
 *   npm run demo -- --goal escalate --max-attempts 4
 *   npm run demo -- --goal impossible
 *   npm run demo -- --goal happy-path --json
 *
 * Exit code 0 if the goal reaches "done", 1 if it escalates.
 */
import { parseArgs } from "node:util";
import { runGoal, type RunReport } from "./coding-agent-pipeline/index.js";
import { STRATEGY_CATALOG, STRATEGY_IMPLEMENTATIONS } from "../demo/mergeConfigStrategies.js";
import { selectDemoGoal } from "../demo/goals.js";
import type { JsonObject } from "./coding-agent-pipeline/jsonUtils.js";

function parseCliArgs(argv: string[]): { goal: string; maxAttempts?: number; json: boolean } {
  const { values } = parseArgs({
    args: argv,
    options: {
      goal: { type: "string", default: "happy-path" },
      "max-attempts": { type: "string" },
      json: { type: "boolean", default: false },
    },
  });

  return {
    goal: values.goal ?? "happy-path",
    maxAttempts: values["max-attempts"] !== undefined ? Number(values["max-attempts"]) : undefined,
    json: values.json ?? false,
  };
}

function printReport(report: RunReport<JsonObject>): void {
  console.log(`GoalSpec: ${report.goalId}`);
  console.log(`Plan: ${report.plan.steps.map((s) => s.strategy.name).join(" -> ") || "<empty>"}`);
  console.log("");

  for (const record of report.attempts) {
    const { validation, decision } = record;
    console.log(
      `[ATTEMPT ${record.attempt}] strategy '${record.strategy.name}' -> ` +
        `${validation.outcomes.length - validation.failedIds.length}/${validation.outcomes.length} checks passed`,
    );
    for (const outcome of validation.outcomes) {
      if (!outcome.passed) console.log(`    FAIL [${outcome.id}] ${outcome.detail}`);
    }
    console.log(`    decision: ${decision.kind}${decision.escalateCause ? ` (${decision.escalateCause})` : ""} — ${decision.reason}`);
    console.log("");
  }

  console.log(`Target files: ${report.targetFiles.join(", ")}`);
  console.log(report.outcome === "done" ? "DONE" : "ESCALATED");
}

async function main(argv: string[]): Promise<number> {
  const args = parseCliArgs(argv);
  const goal = selectDemoGoal(args.goal, args.maxAttempts);
  const report = runGoal(goal, STRATEGY_CATALOG, STRATEGY_IMPLEMENTATIONS);

  if (args.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    printReport(report);
  }

  return report.outcome === "done" ? 0 : 1;
}

main(process.argv.slice(2))
  .then((code) => process.exit(code))
  .catch((err) => {
    console.error(err instanceof Error ? err.message : String(err));
    process.exit(1);
  });
