import { Logger, ValidationPipe } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import helmet from 'helmet';
import { AppModule } from './app.module';
import { AppConfig } from './config/configuration';

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule, {
    bufferLogs: false,
    // Preserve the raw request body so Stripe webhook signatures can be
    // verified (a parsed JSON body fails verification).
    rawBody: true,
  });
  const config = app.get(ConfigService);
  const appConfig = config.getOrThrow<AppConfig>('app');
  const logger = new Logger('Bootstrap');

  // Security headers.
  app.use(helmet());

  // Strict CORS — only the configured origins may call the API from a browser.
  app.enableCors({
    origin: appConfig.corsOrigins,
    credentials: true,
  });

  app.setGlobalPrefix('api');

  // Validate and strip every incoming payload globally.
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: { enableImplicitConversion: true },
    }),
  );

  // Interactive API docs (disabled in production unless explicitly wanted).
  if (appConfig.nodeEnv !== 'production') {
    const swaggerConfig = new DocumentBuilder()
      .setTitle('AI Quran Teacher API')
      .setDescription(
        'Mistral-AI-powered tajweed correction, quizzes, gamification and Quran content.',
      )
      .setVersion('1.0')
      .addBearerAuth()
      .build();
    const document = SwaggerModule.createDocument(app, swaggerConfig);
    SwaggerModule.setup('api/docs', app, document);
  }

  app.enableShutdownHooks();
  await app.listen(appConfig.port);
  logger.log(`AI Quran Teacher API listening on port ${appConfig.port}`);
}

bootstrap().catch((err) => {
  // eslint-disable-next-line no-console
  console.error('Fatal error during bootstrap', err);
  process.exit(1);
});
