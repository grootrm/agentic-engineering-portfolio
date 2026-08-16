/** Structured errors raised by the orchestration core (not by demo/domain code). */

export class UnknownStrategyError extends Error {
  readonly strategyName: string;
  readonly known: string[];

  constructor(strategyName: string, known: string[]) {
    super(`Unknown strategy "${strategyName}" (known strategies: ${known.join(", ") || "<none>"})`);
    this.name = "UnknownStrategyError";
    this.strategyName = strategyName;
    this.known = known;
  }
}

export class InvalidGoalSpecError extends Error {
  readonly goalId: string;
  readonly reasons: string[];

  constructor(goalId: string, reasons: string[]) {
    super(`Invalid GoalSpec "${goalId}": ${reasons.join("; ")}`);
    this.name = "InvalidGoalSpecError";
    this.goalId = goalId;
    this.reasons = reasons;
  }
}
