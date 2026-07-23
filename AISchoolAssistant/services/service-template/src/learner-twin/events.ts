import { z } from 'zod';
import type { EventDefinition } from '@asa/eventing';

export const LESSON_COMPLETED = 'learner.lesson.completed';
export const ASSESSMENT_SCORED = 'learner.assessment.scored';

export const lessonCompletedSchema = z.object({
  learnerId: z.string().min(1),
  lessonId: z.string().min(1),
  topic: z.string().min(1),
});
export const assessmentScoredSchema = z.object({
  learnerId: z.string().min(1),
  assessmentId: z.string().min(1),
  topic: z.string().min(1),
  score: z.number().min(0).max(100),
});

export type LessonCompleted = z.infer<typeof lessonCompletedSchema>;
export type AssessmentScored = z.infer<typeof assessmentScoredSchema>;

/** The learner-domain event definitions registered in the Event Catalog. */
export const learnerEvents: EventDefinition[] = [
  {
    type: LESSON_COMPLETED,
    version: '1',
    schema: lessonCompletedSchema,
    description: 'A learner completed a lesson.',
  },
  {
    type: ASSESSMENT_SCORED,
    version: '1',
    schema: assessmentScoredSchema,
    description: 'A learner received a score on an assessment.',
  },
];
