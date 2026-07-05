import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { TajweedMistake } from './tajweed.entity';
import {
  RULE_DESCRIPTIONS,
  TajweedRuleOccurrence,
  analyzeText,
  normalizeArabic,
} from './tajweed.rules';

export interface DetectedMistake {
  type: 'word_mismatch' | 'missing_word' | 'extra_word';
  severity: 'minor' | 'moderate' | 'major';
  wordIndex: number;
  expectedWord: string;
  actualWord: string;
  suggestion: string;
}

export interface DetectionResult {
  ayahId: number;
  accuracy: number;
  mistakes: DetectedMistake[];
  rulesToObserve: TajweedRuleOccurrence[];
}

type WordOp =
  | { op: 'match'; expectedIndex: number; actualIndex: number }
  | { op: 'substitute'; expectedIndex: number; actualIndex: number }
  | { op: 'delete'; expectedIndex: number }
  | { op: 'insert'; actualIndex: number };

@Injectable()
export class TajweedService {
  constructor(
    @InjectRepository(TajweedMistake)
    private readonly mistakesRepository: Repository<TajweedMistake>,
  ) {}

  /** Static rule catalog, used by clients and the quiz generator. */
  getRules() {
    return Object.entries(RULE_DESCRIPTIONS).map(([rule, description]) => ({
      rule,
      description,
    }));
  }

  /** Finds Tajweed rule occurrences in a vocalized text. */
  analyze(text: string): TajweedRuleOccurrence[] {
    return analyzeText(text);
  }

  /**
   * Compares a recitation transcript against the expected mushaf text,
   * returning word-level mistakes plus the Tajweed rules present in the ayah.
   */
  async detectMistakes(
    text: string,
    ayahId: number,
    expectedText?: string,
    userId?: string,
  ): Promise<DetectionResult> {
    const rulesToObserve = analyzeText(expectedText ?? text);

    if (!expectedText) {
      return { ayahId, accuracy: 1, mistakes: [], rulesToObserve };
    }

    const expectedWords = normalizeArabic(expectedText).split(' ');
    const actualWords = normalizeArabic(text)
      .split(' ')
      .filter((w) => w.length > 0);

    const mistakes: DetectedMistake[] = [];
    let matched = 0;

    for (const op of alignWords(expectedWords, actualWords)) {
      switch (op.op) {
        case 'match':
          matched++;
          break;
        case 'substitute':
          mistakes.push({
            type: 'word_mismatch',
            severity: 'major',
            wordIndex: op.expectedIndex,
            expectedWord: expectedWords[op.expectedIndex],
            actualWord: actualWords[op.actualIndex],
            suggestion: `Expected "${expectedWords[op.expectedIndex]}" but heard "${actualWords[op.actualIndex]}". Listen to the ayah again and repeat slowly.`,
          });
          break;
        case 'delete':
          mistakes.push({
            type: 'missing_word',
            severity: 'major',
            wordIndex: op.expectedIndex,
            expectedWord: expectedWords[op.expectedIndex],
            actualWord: '',
            suggestion: `The word "${expectedWords[op.expectedIndex]}" was skipped.`,
          });
          break;
        case 'insert':
          mistakes.push({
            type: 'extra_word',
            severity: 'moderate',
            wordIndex: op.actualIndex,
            expectedWord: '',
            actualWord: actualWords[op.actualIndex],
            suggestion: `The word "${actualWords[op.actualIndex]}" is not part of this ayah.`,
          });
          break;
      }
    }

    const accuracy =
      expectedWords.length === 0 ? 1 : matched / expectedWords.length;

    if (userId && mistakes.length > 0) {
      await this.mistakesRepository.save(
        mistakes.map((m) =>
          this.mistakesRepository.create({ ...m, userId, ayahId }),
        ),
      );
    }

    return { ayahId, accuracy, mistakes, rulesToObserve };
  }

  /** Mistake history for a user, most recent first. */
  getMistakesForUser(userId: string): Promise<TajweedMistake[]> {
    return this.mistakesRepository.find({
      where: { userId },
      order: { createdAt: 'DESC' },
      take: 100,
    });
  }
}

/**
 * Word-level alignment via Levenshtein with backtrace, so that a single
 * skipped word does not cascade into mismatches for the rest of the ayah.
 */
function alignWords(expected: string[], actual: string[]): WordOp[] {
  const m = expected.length;
  const n = actual.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () =>
    new Array<number>(n + 1).fill(0),
  );
  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      const cost = expected[i - 1] === actual[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(
        dp[i - 1][j - 1] + cost,
        dp[i - 1][j] + 1,
        dp[i][j - 1] + 1,
      );
    }
  }

  const ops: WordOp[] = [];
  let i = m;
  let j = n;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && expected[i - 1] === actual[j - 1]) {
      ops.push({ op: 'match', expectedIndex: i - 1, actualIndex: j - 1 });
      i--;
      j--;
    } else if (i > 0 && j > 0 && dp[i][j] === dp[i - 1][j - 1] + 1) {
      ops.push({ op: 'substitute', expectedIndex: i - 1, actualIndex: j - 1 });
      i--;
      j--;
    } else if (i > 0 && dp[i][j] === dp[i - 1][j] + 1) {
      ops.push({ op: 'delete', expectedIndex: i - 1 });
      i--;
    } else {
      ops.push({ op: 'insert', actualIndex: j - 1 });
      j--;
    }
  }
  return ops.reverse();
}
