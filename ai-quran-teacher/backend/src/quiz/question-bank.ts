import { QuizDifficulty, QuizQuestion } from './quiz.entity';

export type BankQuestion = QuizQuestion & { difficulty: QuizDifficulty };

/**
 * Curated Tajweed question bank. IDs are stable so client apps can
 * deduplicate questions a user has already seen.
 */
export const QUESTION_BANK: BankQuestion[] = [
  {
    id: 'easy-1',
    difficulty: 'easy',
    question: 'How many letters trigger the rule of Ikhfa after noon sakinah or tanween?',
    options: ['6', '10', '15', '28'],
    correctIndex: 2,
    explanation:
      'Ikhfa applies before the 15 letters that remain after excluding the izhar, idgham, and iqlab letters.',
  },
  {
    id: 'easy-2',
    difficulty: 'easy',
    question: 'Which letter triggers Iqlab after noon sakinah or tanween?',
    options: ['ب', 'م', 'ل', 'ر'],
    correctIndex: 0,
    explanation:
      'Iqlab converts the noon sakinah or tanween into a hidden meem when followed by the letter ب.',
  },
  {
    id: 'easy-3',
    difficulty: 'easy',
    question: 'What does "ghunnah" refer to?',
    options: [
      'A nasal sound held for two counts',
      'An echoing bounce on certain letters',
      'Stretching a long vowel',
      'A pause at the end of an ayah',
    ],
    correctIndex: 0,
    explanation:
      'Ghunnah is the nasal sound produced from the nose, most prominent on noon and meem with shadda.',
  },
  {
    id: 'easy-4',
    difficulty: 'easy',
    question: 'How many counts is a natural madd (madd tabee’i) held?',
    options: ['1', '2', '4', '6'],
    correctIndex: 1,
    explanation: 'The natural madd is stretched for two counts (harakah).',
  },
  {
    id: 'medium-1',
    difficulty: 'medium',
    question: 'Which letters are the qalqalah letters?',
    options: ['ق ط ب ج د', 'ء ه ع ح غ خ', 'ي ر م ل و ن', 'ص ض ط ظ'],
    correctIndex: 0,
    explanation:
      'The five qalqalah letters (collected in "قطب جد") produce an echoing bounce when they carry sukoon.',
  },
  {
    id: 'medium-2',
    difficulty: 'medium',
    question: 'Idgham without ghunnah occurs before which letters?',
    options: ['ل and ر', 'ي and و', 'م and ن', 'ب and م'],
    correctIndex: 0,
    explanation:
      'Before ل and ر, the noon sakinah or tanween merges completely without nasalization.',
  },
  {
    id: 'medium-3',
    difficulty: 'medium',
    question: 'The izhar (clear pronunciation) letters are articulated from which area?',
    options: ['The throat', 'The lips', 'The tongue tip', 'The nasal cavity'],
    correctIndex: 0,
    explanation:
      'The six izhar letters (ء ه ع ح غ خ) are all throat letters, so the noon is pronounced clearly before them.',
  },
  {
    id: 'medium-4',
    difficulty: 'medium',
    question: 'In the word "مِنْ بَعْدِ", which rule applies to the noon sakinah?',
    options: ['Iqlab', 'Izhar', 'Ikhfa', 'Idgham'],
    correctIndex: 0,
    explanation:
      'The noon sakinah is followed by ب, so it is converted to a hidden meem with ghunnah (iqlab).',
  },
  {
    id: 'hard-1',
    difficulty: 'hard',
    question: 'Madd muttasil (connected madd) occurs when a madd letter is followed by:',
    options: [
      'A hamza in the same word',
      'A hamza in the next word',
      'A sukoon caused by stopping',
      'A shadda in the same word',
    ],
    correctIndex: 0,
    explanation:
      'Madd muttasil is when the hamza follows the madd letter within the same word; it is stretched 4-5 counts.',
  },
  {
    id: 'hard-2',
    difficulty: 'hard',
    question: 'Which of the following describes madd lazim?',
    options: [
      'A madd letter followed by an original sukoon or shadda, held 6 counts',
      'A madd letter at the end of an ayah, held 2 counts',
      'A madd letter followed by hamza in the next word',
      'A shortened madd when connecting two words',
    ],
    correctIndex: 0,
    explanation:
      'Madd lazim occurs when a permanent sukoon or shadda follows the madd letter and must be held six counts.',
  },
  {
    id: 'hard-3',
    difficulty: 'hard',
    question: 'Idgham of noon sakinah does NOT apply within a single word (e.g. دُنْيَا). Why?',
    options: [
      'To avoid confusing the word with a doubled-letter root',
      'Because the noon is part of a prefix',
      'Because ghunnah is forbidden mid-word',
      'It actually does apply within a single word',
    ],
    correctIndex: 0,
    explanation:
      'In words like دُنْيَا and قِنْوَان, izhar is applied instead of idgham to preserve the word’s distinct meaning; this is called izhar mutlaq.',
  },
  {
    id: 'hard-4',
    difficulty: 'hard',
    question: 'When stopping on a qalqalah letter with shadda (e.g. الْحَقّ), the qalqalah is:',
    options: [
      'Strongest (qalqalah kubra with shadda emphasis)',
      'Omitted entirely',
      'The same as mid-word qalqalah',
      'Replaced with ghunnah',
    ],
    correctIndex: 0,
    explanation:
      'Stopping on a doubled qalqalah letter produces the strongest level of qalqalah.',
  },
];
