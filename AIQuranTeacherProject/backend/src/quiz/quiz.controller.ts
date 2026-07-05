import {
  Body,
  Controller,
  Get,
  Param,
  ParseUUIDPipe,
  Post,
} from '@nestjs/common';
import { ApiBearerAuth, ApiOperation, ApiTags } from '@nestjs/swagger';
import { Throttle } from '@nestjs/throttler';
import {
  AuthenticatedUser,
  CurrentUser,
} from '../common/decorators/current-user.decorator';
import { GenerateQuizDto } from './dto/generate-quiz.dto';
import { SubmitQuizDto } from './dto/submit-quiz.dto';
import { PublicQuiz, QuizResult, QuizService } from './quiz.service';

@ApiTags('quiz')
@ApiBearerAuth()
@Controller('quiz')
export class QuizController {
  constructor(private readonly quizService: QuizService) {}

  @Throttle({ default: { limit: 20, ttl: 60_000 } })
  @Post('generate')
  @ApiOperation({ summary: 'Generate a new AI quiz.' })
  generate(
    @CurrentUser() user: AuthenticatedUser,
    @Body() dto: GenerateQuizDto,
  ): Promise<PublicQuiz> {
    return this.quizService.generate(user.userId, dto);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Fetch a quiz (without correct answers).' })
  get(
    @CurrentUser() user: AuthenticatedUser,
    @Param('id', ParseUUIDPipe) id: string,
  ): Promise<PublicQuiz> {
    return this.quizService.getForUser(user.userId, id);
  }

  @Post(':id/submit')
  @ApiOperation({ summary: 'Submit answers and receive a graded result.' })
  submit(
    @CurrentUser() user: AuthenticatedUser,
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: SubmitQuizDto,
  ): Promise<QuizResult> {
    return this.quizService.submit(user.userId, id, dto);
  }
}
