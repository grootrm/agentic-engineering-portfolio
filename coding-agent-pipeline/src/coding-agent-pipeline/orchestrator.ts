import { decide, type CriticDecision } from "./critic.js";
import { executeStrategy, type ExecutionResult, type StrategyFn } from "./executor.js";
import type { GoalSpec } from "./goalSpec.js";
import type { JsonObject } from "./jsonUtils.js";
import { planStrategies } from "./planner.js";
import type { Plan, Strategy } from "./strategy.js";
import { validate, type ValidationReport } from "./validator.js";
import { validateGoalSpec } from "./validateGoalSpec.js";

export interface AttemptRecord<TOutput extends JsonObject = JsonObject> {
  readonly attempt: number;
  readonly strategy: Strategy;
  readonly execution: ExecutionResult<TOutput>;
  readonly validation: ValidationReport;
  readonly decision: CriticDecision;
}

export interface RunReport<TOutput extends JsonObject = JsonObject> {
  readonly goalId: string;
  readonly targetFiles: string[];
  readonly plan: Plan;
  readonly attempts: AttemptRecord<TOutput>[];
  readonly outcome: "done" | "escalated";
  readonly finalDecision: CriticDecision;
}

/**
 * Runs the full Planner -> Executor -> Validator -> Critic loop for `goal`, trying each
 * planned strategy in order until the Critic declares the goal done or escalates.
 * Throws InvalidGoalSpecError before recording any attempts if `goal` is malformed.
 */
export function runGoal<TInput, TOutput extends JsonObject = JsonObject>(
  goal: GoalSpec<TInput>,
  catalog: Strategy[],
  implementations: Record<string, StrategyFn<TInput, TOutput>>,
): RunReport<TOutput> {
  validateGoalSpec(goal);

  const plan = planStrategies(goal, catalog);

  if (plan.steps.length === 0) {
    const decision: CriticDecision = {
      kind: "escalate",
      attempt: 0,
      reason: "no candidate strategies matched the goal's required capabilities",
      escalateCause: "strategies-exhausted",
      diagnostics: goal.acceptanceCriteria.map((c) => c.id),
    };
    return { goalId: goal.id, targetFiles: goal.targetFiles, plan, attempts: [], outcome: "escalated", finalDecision: decision };
  }

  const attempts: AttemptRecord<TOutput>[] = [];

  for (let index = 0; index < plan.steps.length; index += 1) {
    const step = plan.steps[index];
    if (!step) break; // unreachable given the loop bound; satisfies noUncheckedIndexedAccess

    const attemptNumber = index + 1;
    const execution = executeStrategy<TInput, TOutput>(attemptNumber, step.strategy.name, implementations, goal.scenario);
    const validation = validate(goal, execution);
    const remainingSteps = plan.steps.slice(index + 1);
    const decision = decide(goal, remainingSteps, attemptNumber, validation);

    attempts.push({ attempt: attemptNumber, strategy: step.strategy, execution, validation, decision });

    if (decision.kind !== "retry") {
      return {
        goalId: goal.id,
        targetFiles: goal.targetFiles,
        plan,
        attempts,
        outcome: decision.kind === "done" ? "done" : "escalated",
        finalDecision: decision,
      };
    }
  }

  // Unreachable in practice: the Critic only returns "retry" when a next step exists in
  // `plan.steps`, so the loop above always returns from within before falling off the end.
  // This fallback exists to keep runGoal total and satisfy strict control-flow analysis.
  const lastAttempt = attempts[attempts.length - 1];
  if (!lastAttempt) {
    throw new Error("unreachable: runGoal's loop exited without recording any attempts");
  }
  return {
    goalId: goal.id,
    targetFiles: goal.targetFiles,
    plan,
    attempts,
    outcome: "escalated",
    finalDecision: lastAttempt.decision,
  };
}
