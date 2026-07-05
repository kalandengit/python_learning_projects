import { RevelationPlace } from './entities/surah.entity';

export interface SeedAyah {
  numberInSurah: number;
  textArabic: string;
  textTransliteration: string;
  translation: string;
}

export interface SeedSurah {
  id: number;
  nameArabic: string;
  nameTransliteration: string;
  nameTranslation: string;
  revelationPlace: RevelationPlace;
  ayahCount: number;
  ayahs: SeedAyah[];
}

/**
 * A minimal, offline seed so the API is useful out of the box without an
 * external Quran dataset. Extend by importing a full corpus in a migration.
 * Translation follows the widely-used Saheeh International rendering.
 */
export const QURAN_SEED: SeedSurah[] = [
  {
    id: 1,
    nameArabic: 'الفاتحة',
    nameTransliteration: 'Al-Fatihah',
    nameTranslation: 'The Opening',
    revelationPlace: RevelationPlace.Meccan,
    ayahCount: 7,
    ayahs: [
      {
        numberInSurah: 1,
        textArabic: 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
        textTransliteration: 'Bismi Allāhi ar-raḥmāni ar-raḥīm',
        translation:
          'In the name of Allah, the Entirely Merciful, the Especially Merciful.',
      },
      {
        numberInSurah: 2,
        textArabic: 'الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ',
        textTransliteration: 'Al-ḥamdu lillāhi rabbi al-ʿālamīn',
        translation: 'All praise is due to Allah, Lord of the worlds.',
      },
      {
        numberInSurah: 3,
        textArabic: 'الرَّحْمَٰنِ الرَّحِيمِ',
        textTransliteration: 'Ar-raḥmāni ar-raḥīm',
        translation: 'The Entirely Merciful, the Especially Merciful.',
      },
      {
        numberInSurah: 4,
        textArabic: 'مَالِكِ يَوْمِ الدِّينِ',
        textTransliteration: 'Māliki yawmi ad-dīn',
        translation: 'Sovereign of the Day of Recompense.',
      },
      {
        numberInSurah: 5,
        textArabic: 'إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ',
        textTransliteration: 'Iyyāka naʿbudu wa-iyyāka nastaʿīn',
        translation: 'It is You we worship and You we ask for help.',
      },
      {
        numberInSurah: 6,
        textArabic: 'اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ',
        textTransliteration: 'Ihdinā aṣ-ṣirāṭa al-mustaqīm',
        translation: 'Guide us to the straight path.',
      },
      {
        numberInSurah: 7,
        textArabic:
          'صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ',
        textTransliteration:
          'Ṣirāṭa alladhīna anʿamta ʿalayhim ghayri al-maghḍūbi ʿalayhim wa-lā aḍ-ḍāllīn',
        translation:
          'The path of those upon whom You have bestowed favor, not of those who have earned Your anger or of those who are astray.',
      },
    ],
  },
  {
    id: 112,
    nameArabic: 'الإخلاص',
    nameTransliteration: 'Al-Ikhlas',
    nameTranslation: 'Sincerity',
    revelationPlace: RevelationPlace.Meccan,
    ayahCount: 4,
    ayahs: [
      {
        numberInSurah: 1,
        textArabic: 'قُلْ هُوَ اللَّهُ أَحَدٌ',
        textTransliteration: 'Qul huwa Allāhu aḥad',
        translation: 'Say, "He is Allah, [who is] One,',
      },
      {
        numberInSurah: 2,
        textArabic: 'اللَّهُ الصَّمَدُ',
        textTransliteration: 'Allāhu aṣ-ṣamad',
        translation: 'Allah, the Eternal Refuge.',
      },
      {
        numberInSurah: 3,
        textArabic: 'لَمْ يَلِدْ وَلَمْ يُولَدْ',
        textTransliteration: 'Lam yalid wa-lam yūlad',
        translation: 'He neither begets nor is born,',
      },
      {
        numberInSurah: 4,
        textArabic: 'وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ',
        textTransliteration: 'Wa-lam yakun lahu kufuwan aḥad',
        translation: 'Nor is there to Him any equivalent."',
      },
    ],
  },
];
