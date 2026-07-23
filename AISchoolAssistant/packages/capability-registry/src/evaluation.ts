/** Outcome of a single assertion within an evaluation case. */
export interface AssertionResult {
  passed: boolean;
  detail?: string;
}

/**
 * One evaluation case: an input and an assertion over the produced output. The
 * assertion may return a boolean or a detailed result. Cases are deterministic
 * when run against a deterministic provider (e.g. the EchoProvider), giving a
 * reproducible quality gate.
 */
export interface EvaluationCase<Input, Output> {
  name: string;
  input: Input;
  assert: (output: Output, input: Input) => boolean | AssertionResult;
}

/**
 * The evaluation suite that gates a capability. A capability may only be
 * promoted to `published` when the measured pass rate is at least
 * {@link minPassRate}.
 */
export interface EvaluationSuite<Input, Output> {
  /** Minimum fraction of cases that must pass, in [0, 1]. */
  minPassRate: number;
  cases: EvaluationCase<Input, Output>[];
}

/** Per-case result within an evaluation report. */
export interface EvaluationCaseResult {
  name: string;
  passed: boolean;
  detail?: string;
}

/** Aggregate result of running a capability's evaluation suite. */
export interface EvaluationReport {
  capabilityId: string;
  version: string;
  total: number;
  passed: number;
  passRate: number;
  threshold: number;
  /** True when passRate >= threshold. */
  ok: boolean;
  cases: EvaluationCaseResult[];
}

function normalize(result: boolean | AssertionResult): AssertionResult {
  return typeof result === 'boolean' ? { passed: result } : result;
}

/**
 * Summarize per-case outcomes into an {@link EvaluationReport}. Kept pure and
 * separate from execution so it is trivially testable and reused by the runner.
 */
export function summarizeEvaluation(
  capabilityId: string,
  version: string,
  threshold: number,
  cases: EvaluationCaseResult[],
): EvaluationReport {
  const total = cases.length;
  const passed = cases.filter((c) => c.passed).length;
  const passRate = total === 0 ? 0 : passed / total;
  return {
    capabilityId,
    version,
    total,
    passed,
    passRate,
    threshold,
    ok: total > 0 && passRate >= threshold,
    cases,
  };
}

export { normalize as normalizeAssertion };
