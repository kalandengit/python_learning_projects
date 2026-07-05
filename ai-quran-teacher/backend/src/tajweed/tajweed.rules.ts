/**
 * Rule-based Tajweed analysis over fully vocalized (mushaf) Arabic text.
 *
 * This is the deterministic first tier of the Tajweed Engine. A trained
 * audio model can later replace or augment `analyzeText` — the public
 * shapes (`TajweedRuleOccurrence`) are designed to stay stable.
 */

export const DIACRITICS = /[ً-ٰٟۖ-ۭ]/g;
export const TATWEEL = /ـ/g;

export const SUKOON = 'ْ';
export const SHADDA = 'ّ';
export const FATHA = 'َ';
export const DAMMA = 'ُ';
export const KASRA = 'ِ';
export const FATHATAN = 'ً';
export const DAMMATAN = 'ٌ';
export const KASRATAN = 'ٍ';

export const NOON = 'ن';
export const MEEM = 'م';
export const BA = 'ب';

export const ALEF = 'ا';
export const ALEF_MADDA = 'آ';
export const WAW = 'و';
export const YA = 'ي';

const TANWEEN = new Set([FATHATAN, DAMMATAN, KASRATAN]);
const HAMZA_FORMS = new Set(['ء', 'أ', 'إ', 'ئ', 'ؤ', ALEF_MADDA]);

const IZHAR_LETTERS = new Set(['ء', 'أ', 'إ', 'ئ', 'ؤ', 'ه', 'ع', 'ح', 'غ', 'خ']);
const IDGHAM_GHUNNAH_LETTERS = new Set(['ي', 'ن', 'م', 'و']);
const IDGHAM_NO_GHUNNAH_LETTERS = new Set(['ل', 'ر']);
const IQLAB_LETTERS = new Set([BA]);
const QALQALAH_LETTERS = new Set(['ق', 'ط', 'ب', 'ج', 'د']);

const ARABIC_LETTER = /[ء-ي]/;

export type TajweedRuleName =
  | 'izhar'
  | 'idgham_with_ghunnah'
  | 'idgham_without_ghunnah'
  | 'iqlab'
  | 'ikhfa'
  | 'qalqalah'
  | 'ghunnah'
  | 'madd_tabeei'
  | 'madd_faree';

export interface TajweedRuleOccurrence {
  rule: TajweedRuleName;
  /** Index of the triggering character in the original (vocalized) text. */
  position: number;
  /** The character(s) that trigger the rule. */
  trigger: string;
  description: string;
}

export const RULE_DESCRIPTIONS: Record<TajweedRuleName, string> = {
  izhar:
    'Izhar: pronounce the noon sakinah/tanween clearly, without nasalization, before throat letters.',
  idgham_with_ghunnah:
    'Idgham with ghunnah: merge the noon sakinah/tanween into the next letter with nasalization (ي ن م و).',
  idgham_without_ghunnah:
    'Idgham without ghunnah: merge the noon sakinah/tanween into the next letter without nasalization (ل ر).',
  iqlab:
    'Iqlab: convert the noon sakinah/tanween into a hidden meem before ب, with ghunnah.',
  ikhfa:
    'Ikhfa: hide the noon sakinah/tanween with light nasalization before the 15 ikhfa letters.',
  qalqalah:
    'Qalqalah: give an echoing bounce to ق ط ب ج د when they carry sukoon.',
  ghunnah:
    'Ghunnah: hold the nasal sound for two counts on noon or meem with shadda.',
  madd_tabeei:
    'Natural madd: stretch the long vowel for two counts.',
  madd_faree:
    'Extended madd: stretch the long vowel four to five counts when followed by hamza.',
};

const DIACRITIC_CHAR = /[ً-ٰٟۖ-ۭ]/;

/**
 * True if the diacritic cluster attached to the letter at `letterIndex`
 * contains `mark`. Combining marks can appear in any order (e.g. shadda
 * before or after a harakah), so the whole cluster is scanned.
 */
function clusterHas(text: string, letterIndex: number, mark: string): boolean {
  for (let i = letterIndex + 1; i < text.length; i++) {
    if (!DIACRITIC_CHAR.test(text[i])) return false;
    if (text[i] === mark) return true;
  }
  return false;
}

/** Returns the next Arabic base letter at or after `from`, skipping diacritics and spaces. */
function nextBaseLetter(
  text: string,
  from: number,
): { letter: string; index: number } | null {
  for (let i = from; i < text.length; i++) {
    if (ARABIC_LETTER.test(text[i])) {
      return { letter: text[i], index: i };
    }
  }
  return null;
}

function classifyNoonSakinah(
  nextLetter: string,
): TajweedRuleName {
  if (IZHAR_LETTERS.has(nextLetter)) return 'izhar';
  if (IDGHAM_GHUNNAH_LETTERS.has(nextLetter)) return 'idgham_with_ghunnah';
  if (IDGHAM_NO_GHUNNAH_LETTERS.has(nextLetter)) return 'idgham_without_ghunnah';
  if (IQLAB_LETTERS.has(nextLetter)) return 'iqlab';
  return 'ikhfa';
}

/** Detects Tajweed rule occurrences in a fully vocalized Arabic text. */
export function analyzeText(text: string): TajweedRuleOccurrence[] {
  const occurrences: TajweedRuleOccurrence[] = [];

  for (let i = 0; i < text.length; i++) {
    const char = text[i];

    // Noon sakinah (نْ) and tanween share the same four-way ruling.
    const isNoonSakinah = char === NOON && clusterHas(text, i, SUKOON);
    const isTanween = TANWEEN.has(char);
    if (isNoonSakinah || isTanween) {
      const following = nextBaseLetter(text, i + 1);
      if (following) {
        const rule = classifyNoonSakinah(following.letter);
        occurrences.push({
          rule,
          position: i,
          trigger: isNoonSakinah ? NOON + SUKOON : char,
          description: RULE_DESCRIPTIONS[rule],
        });
      }
      continue;
    }

    if (QALQALAH_LETTERS.has(char) && clusterHas(text, i, SUKOON)) {
      occurrences.push({
        rule: 'qalqalah',
        position: i,
        trigger: char + SUKOON,
        description: RULE_DESCRIPTIONS.qalqalah,
      });
      continue;
    }

    if ((char === NOON || char === MEEM) && clusterHas(text, i, SHADDA)) {
      occurrences.push({
        rule: 'ghunnah',
        position: i,
        trigger: char + SHADDA,
        description: RULE_DESCRIPTIONS.ghunnah,
      });
      continue;
    }

    // Madd: long vowel formed by a harakah followed by its matching letter.
    const prev = text[i - 1] ?? '';
    const isMadd =
      char === ALEF_MADDA ||
      (char === ALEF && prev === FATHA) ||
      (char === WAW && prev === DAMMA) ||
      (char === YA && prev === KASRA);
    if (isMadd) {
      const following = nextBaseLetter(text, i + 1);
      const extended = following !== null && HAMZA_FORMS.has(following.letter);
      const rule: TajweedRuleName = extended ? 'madd_faree' : 'madd_tabeei';
      occurrences.push({
        rule,
        position: i,
        trigger: char,
        description: RULE_DESCRIPTIONS[rule],
      });
    }
  }

  return occurrences;
}

/** Strips diacritics and normalizes letter variants for word comparison. */
export function normalizeArabic(text: string): string {
  return text
    .replace(DIACRITICS, '')
    .replace(TATWEEL, '')
    .replace(/[أإآٱ]/g, ALEF)
    .replace(/ى/g, YA)
    .replace(/\s+/g, ' ')
    .trim();
}
