import type { CapabilityDefinition } from './capability';
import {
  normalizeAssertion,
  summarizeEvaluation,
  type EvaluationCaseResult,
  type EvaluationReport,
} from './evaluation';
import { executeCapability, type ExecutionDeps } from './execution';

/**
 * Runs a capability's evaluation suite by executing each case through the same
 * governed path used in production, then applying the case assertion. Produces
 * a reproducible {@link EvaluationReport}. A case that throws (e.g. schema or
 * governance failure) is recorded as failed rather than aborting the run.
 */
export async function evaluateCapability<Input, Output>(
  definition: CapabilityDefinition<Input, Output>,
  deps: ExecutionDeps,
): Promise<EvaluationReport> {
  const { cases, minPassRate } = definition.evaluation;
  const results: EvaluationCaseResult[] = [];

  for (const testCase of cases) {
    try {
      const { output } = await executeCapability(
        definition,
        testCase.input,
        {},
        deps,
      );
      const assertion = normalizeAssertion(
        testCase.assert(output, testCase.input),
      );
      results.push({
        name: testCase.name,
        passed: assertion.passed,
        detail: assertion.detail,
      });
    } catch (error) {
      results.push({
        name: testCase.name,
        passed: false,
        detail:
          error instanceof Error ? error.message : 'threw during execution',
      });
    }
  }

  return summarizeEvaluation(
    definition.id,
    definition.version,
    minPassRate,
    results,
  );
}
