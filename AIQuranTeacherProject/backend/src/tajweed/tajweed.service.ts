import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { ChatMessage, MistralService } from '../common/mistral/mistral.service';
import { QuranService } from '../quran/quran.service';
import { AnalyzeRecitationDto } from './dto/analyze-recitation.dto';
import {
  MistakeSeverity,
  TajweedAnalysis,
  TajweedMistake,
} from './tajweed.entity';

/** Shape the AI is instructed to return. Validated before persistence. */
interface AiTajweedResult {
  score: number;
  feedback: string;
  mistakes: TajweedMistake[];
}

const SYSTEM_PROMPT = `You are an expert Quran teacher specialised in tajweed (the rules of Quranic recitation).
You will receive the correct Arabic text of an ayah and a transcript of a student's recitation.
Compare them and identify tajweed and pronunciation mistakes.

Respond ONLY with a JSON object matching exactly this TypeScript type:
{
  "score": number,            // overall accuracy 0-100
  "feedback": string,         // 1-2 short encouraging sentences for the student
  "mistakes": Array<{
    "word": string,           // the Arabic word or fragment involved
    "position": number | null,// 1-based word index in the ayah, or null
    "rule": string,           // tajweed rule, e.g. "Ikhfa", "Madd", "Qalqalah", "Ghunnah"
    "severity": "minor" | "moderate" | "major",
    "explanation": string,    // why it is a mistake, in plain language
    "correction": string      // how to say it correctly
  }>
}

Be encouraging and precise. If the recitation is essentially correct, return an empty mistakes array and a high score. Do not include any text outside the JSON object.`;

@Injectable()
export class TajweedService {
  private readonly logger = new Logger(TajweedService.name);

  constructor(
    @InjectRepository(TajweedAnalysis)
    private readonly analyses: Repository<TajweedAnalysis>,
    private readonly mistral: MistralService,
    private readonly quran: QuranService,
  ) {}

  /**
   * Analyse a learner's recitation of a specific ayah and persist the result.
   * Throws NotFound (via QuranService) if the ayah does not exist.
   */
  async analyze(
    userId: string,
    dto: AnalyzeRecitationDto,
  ): Promise<TajweedAnalysis> {
    const ayah = await this.quran.getAyah(dto.surahId, dto.ayahNumber);

    const messages: ChatMessage[] = [
      { role: 'system', content: SYSTEM_PROMPT },
      {
        role: 'user',
        content: [
          `Correct ayah (Arabic): ${ayah.textArabic}`,
          ayah.textTransliteration
            ? `Transliteration: ${ayah.textTransliteration}`
            : '',
          `Student recitation transcript: ${dto.transcript}`,
        ]
          .filter(Boolean)
          .join('\n'),
      },
    ];

    const result = await this.mistral.chatJson<AiTajweedResult>(messages, {
      temperature: 0.1,
    });

    const analysis = this.analyses.create({
      userId,
      surahId: dto.surahId,
      ayahNumber: dto.ayahNumber,
      referenceText: ayah.textArabic,
      transcript: dto.transcript,
      score: this.clampScore(result.score),
      feedback: result.feedback ?? '',
      mistakes: this.sanitizeMistakes(result.mistakes),
    });

    return this.analyses.save(analysis);
  }

  /** A learner's most recent analyses, newest first. */
  history(userId: string, limit = 20): Promise<TajweedAnalysis[]> {
    return this.analyses.find({
      where: { userId },
      order: { createdAt: 'DESC' },
      take: Math.min(Math.max(limit, 1), 100),
    });
  }

  private clampScore(score: unknown): number {
    const n = Number(score);
    if (!Number.isFinite(n)) return 0;
    return Math.round(Math.min(100, Math.max(0, n)));
  }

  /** Defensive normalisation — never trust the model's output blindly. */
  private sanitizeMistakes(mistakes: unknown): TajweedMistake[] {
    if (!Array.isArray(mistakes)) return [];
    const valid = new Set<string>(Object.values(MistakeSeverity));
    return mistakes.slice(0, 50).map((m) => {
      const raw = (m ?? {}) as Record<string, unknown>;
      const severity = String(raw.severity);
      return {
        word: String(raw.word ?? '').slice(0, 200),
        position:
          raw.position === null || raw.position === undefined
            ? null
            : Number(raw.position),
        rule: String(raw.rule ?? 'Unknown').slice(0, 100),
        severity: valid.has(severity)
          ? (severity as MistakeSeverity)
          : MistakeSeverity.Minor,
        explanation: String(raw.explanation ?? '').slice(0, 1000),
        correction: String(raw.correction ?? '').slice(0, 1000),
      };
    });
  }
}
