import { Body, Controller, Get, Param, ParseUUIDPipe, Post } from '@nestjs/common';
import { GenerateQuizDto, SubmitQuizDto } from './quiz.dto';
import { QuizService } from './quiz.service';

@Controller('quiz')
export class QuizController {
  constructor(private readonly quizService: QuizService) {}

  @Post('generate')
  generate(@Body() dto: GenerateQuizDto) {
    return this.quizService.generateQuiz(dto.userId, dto.difficulty, dto.count);
  }

  @Post('submit')
  submit(@Body() dto: SubmitQuizDto) {
    return this.quizService.submitQuiz(dto.quizId, dto.answers);
  }

  @Get('history/:userId')
  history(@Param('userId', ParseUUIDPipe) userId: string) {
    return this.quizService.getHistory(userId);
  }
}
