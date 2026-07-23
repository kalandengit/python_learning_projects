import { Inject, Injectable, type OnModuleInit } from '@nestjs/common';
import { EVENT_BUS, type DomainEvent, type EventBus } from '@asa/eventing';
import { NotFoundError } from '@asa/errors';
import {
  ASSESSMENT_SCORED,
  LESSON_COMPLETED,
  type AssessmentScored,
  type LessonCompleted,
} from './events';

/** The Learner Digital Twin: an evolving projection of a learner's activity. */
export interface LearnerTwin {
  learnerId: string;
  lessonsCompleted: number;
  assessmentsTaken: number;
  averageScore: number;
  /** Latest score per topic (a coarse mastery signal). */
  masteryByTopic: Record<string, number>;
  lastActivityAt?: string;
}

/**
 * Builds and serves the Learner Digital Twin by projecting domain events. It
 * subscribes to the event bus on startup and folds each event into an
 * in-memory projection — the read model is never written directly, only
 * derived from events (event-driven, CQRS-style). Swap the in-memory map for a
 * persistent read store without touching publishers.
 */
@Injectable()
export class LearnerTwinService implements OnModuleInit {
  private readonly twins = new Map<string, LearnerTwin>();
  private scoreTotals = new Map<string, { sum: number; count: number }>();

  constructor(@Inject(EVENT_BUS) private readonly bus: EventBus) {}

  onModuleInit(): void {
    this.bus.subscribe(LESSON_COMPLETED, (event) =>
      this.onLessonCompleted(event),
    );
    this.bus.subscribe(ASSESSMENT_SCORED, (event) =>
      this.onAssessmentScored(event),
    );
  }

  get(learnerId: string): LearnerTwin {
    const twin = this.twins.get(learnerId);
    if (!twin) {
      throw new NotFoundError(`No digital twin for learner "${learnerId}".`);
    }
    return twin;
  }

  private ensure(learnerId: string, at: string): LearnerTwin {
    let twin = this.twins.get(learnerId);
    if (!twin) {
      twin = {
        learnerId,
        lessonsCompleted: 0,
        assessmentsTaken: 0,
        averageScore: 0,
        masteryByTopic: {},
      };
      this.twins.set(learnerId, twin);
    }
    twin.lastActivityAt = at;
    return twin;
  }

  private onLessonCompleted(event: DomainEvent): void {
    const data = event.data as LessonCompleted;
    const twin = this.ensure(data.learnerId, event.occurredAt);
    twin.lessonsCompleted += 1;
    twin.masteryByTopic[data.topic] ??= 0;
  }

  private onAssessmentScored(event: DomainEvent): void {
    const data = event.data as AssessmentScored;
    const twin = this.ensure(data.learnerId, event.occurredAt);
    twin.assessmentsTaken += 1;
    twin.masteryByTopic[data.topic] = data.score;

    const totals = this.scoreTotals.get(data.learnerId) ?? { sum: 0, count: 0 };
    totals.sum += data.score;
    totals.count += 1;
    this.scoreTotals.set(data.learnerId, totals);
    twin.averageScore = Math.round((totals.sum / totals.count) * 100) / 100;
  }
}
