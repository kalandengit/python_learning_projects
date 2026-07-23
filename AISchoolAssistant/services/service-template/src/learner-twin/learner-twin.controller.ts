import { Body, Controller, Get, Param, Post } from '@nestjs/common';
import { ApiBearerAuth, ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { EventPublisher } from '@asa/eventing';
import { RequestContextService } from '@asa/auth';
import {
  ASSESSMENT_SCORED,
  LESSON_COMPLETED,
  type AssessmentScored,
  type LessonCompleted,
} from './events';
import { LearnerTwinService, type LearnerTwin } from './learner-twin.service';
import { RecordLessonDto } from './dto/record-lesson.dto';
import { RecordAssessmentDto } from './dto/record-assessment.dto';

/**
 * Records learning activity as domain events and serves the resulting Digital
 * Twin. Writes go through the catalog-validated {@link EventPublisher}; the
 * twin is a projection updated by the bus subscription — this endpoint never
 * mutates the read model directly. With the in-process bus the projection is
 * up to date by the time the publish resolves.
 */
@ApiTags('learners')
@ApiBearerAuth()
@Controller('learners')
export class LearnerTwinController {
  constructor(
    private readonly publisher: EventPublisher,
    private readonly twins: LearnerTwinService,
    private readonly context: RequestContextService,
  ) {}

  @Post(':id/lessons')
  @ApiOkResponse({ description: 'The updated learner digital twin.' })
  async recordLesson(
    @Param('id') id: string,
    @Body() body: RecordLessonDto,
  ): Promise<LearnerTwin> {
    await this.publisher.publish<LessonCompleted>({
      type: LESSON_COMPLETED,
      data: { learnerId: id, lessonId: body.lessonId, topic: body.topic },
      subject: id,
      ...this.origin(),
    });
    return this.twins.get(id);
  }

  @Post(':id/assessments')
  @ApiOkResponse({ description: 'The updated learner digital twin.' })
  async recordAssessment(
    @Param('id') id: string,
    @Body() body: RecordAssessmentDto,
  ): Promise<LearnerTwin> {
    await this.publisher.publish<AssessmentScored>({
      type: ASSESSMENT_SCORED,
      data: {
        learnerId: id,
        assessmentId: body.assessmentId,
        topic: body.topic,
        score: body.score,
      },
      subject: id,
      ...this.origin(),
    });
    return this.twins.get(id);
  }

  @Get(':id/twin')
  @ApiOkResponse({ description: 'The learner digital twin projection.' })
  twin(@Param('id') id: string): LearnerTwin {
    return this.twins.get(id);
  }

  private origin(): {
    tenantId?: string;
    actor?: string;
    correlationId?: string;
  } {
    return {
      tenantId: this.context.tenantId,
      actor: this.context.principal?.subject,
      correlationId: this.context.correlationId,
    };
  }
}
