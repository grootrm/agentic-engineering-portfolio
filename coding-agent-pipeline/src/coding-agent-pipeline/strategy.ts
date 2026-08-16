/** Pure data describing a candidate strategy and the plan the Planner produces from a catalog. */

export interface Strategy {
  readonly name: string;
  readonly description: string;
  readonly capabilities: string[];
  /** Ascending = cheaper/simpler; the Planner prefers lower cost among relevant candidates. */
  readonly cost: number;
}

export interface PlanStep {
  readonly attempt: number;
  readonly strategy: Strategy;
  readonly matchedCapabilities: string[];
}

export interface Plan {
  readonly goalId: string;
  readonly steps: PlanStep[];
}
