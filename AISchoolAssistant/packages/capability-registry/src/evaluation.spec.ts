import { summarizeEvaluation } from './evaluation';
import { evaluateCapability } from './evaluation-runner';
import { faqCapability, testDeps } from './testing/fixtures';

describe('summarizeEvaluation', () => {
  it('computes pass rate and ok against the threshold', () => {
    const report = summarizeEvaluation('c', '1.0.0', 0.5, [
      { name: 'a', passed: true },
      { name: 'b', passed: false },
    ]);
    expect(report.passRate).toBe(0.5);
    expect(report.ok).toBe(true);
  });

  it('is not ok when below threshold', () => {
    const report = summarizeEvaluation('c', '1.0.0', 0.9, [
      { name: 'a', passed: true },
      { name: 'b', passed: false },
    ]);
    expect(report.ok).toBe(false);
  });

  it('is not ok with zero cases', () => {
    expect(summarizeEvaluation('c', '1.0.0', 0, []).ok).toBe(false);
  });
});

describe('evaluateCapability', () => {
  it('passes for a well-behaved capability', async () => {
    const report = await evaluateCapability(faqCapability(), testDeps());
    expect(report.total).toBe(2);
    expect(report.passed).toBe(2);
    expect(report.ok).toBe(true);
  });

  it('records a failing case instead of throwing', async () => {
    const capability = faqCapability({
      evaluation: {
        minPassRate: 1,
        cases: [
          {
            name: 'impossible',
            input: { question: 'x' },
            assert: () => false,
          },
        ],
      },
    });
    const report = await evaluateCapability(capability, testDeps());
    expect(report.ok).toBe(false);
    expect(report.cases[0].passed).toBe(false);
  });

  it('marks a case failed when execution throws (e.g. governance)', async () => {
    const capability = faqCapability({
      governance: {
        owner: 'x',
        dataClassification: 'internal',
        pii: false,
        modelAllowList: [],
      },
    });
    const report = await evaluateCapability(capability, testDeps());
    expect(report.passed).toBe(0);
    expect(report.cases[0].detail).toMatch(/allow-list/);
  });
});
