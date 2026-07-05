import { Body, Controller, Get, Param, ParseUUIDPipe, Post } from '@nestjs/common';
import { StartExamDto, SubmitExamDto } from './exam.dto';
import { ExamService } from './exam.service';

@Controller('exams')
export class ExamController {
  constructor(private readonly examService: ExamService) {}

  @Post('start')
  start(@Body() dto: StartExamDto) {
    return this.examService.startExam(dto.userId, dto.level);
  }

  @Post('submit')
  submit(@Body() dto: SubmitExamDto) {
    return this.examService.submitExam(dto.examId, dto.answers);
  }

  @Get('history/:userId')
  history(@Param('userId', ParseUUIDPipe) userId: string) {
    return this.examService.getHistory(userId);
  }

  @Get('certificates/:userId')
  certificates(@Param('userId', ParseUUIDPipe) userId: string) {
    return this.examService.getCertificates(userId);
  }

  /** Public endpoint: verify a certificate by its code. */
  @Get('verify/:code')
  verify(@Param('code') code: string) {
    return this.examService.verifyCertificate(code);
  }
}
