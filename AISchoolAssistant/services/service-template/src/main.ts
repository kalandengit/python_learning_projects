import 'reflect-metadata';
import {
  INestApplication,
  ValidationPipe,
  VersioningType,
} from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import helmet from 'helmet';
import { createLogger } from '@asa/logger';
import { AppModule } from './app.module';
import { APP_CONFIG, type AppConfig } from './config/app-config';

const GLOBAL_PREFIX = 'api';

/** Configure the HTTP surface: security headers, versioning, validation, docs. */
export function configureApp(app: INestApplication, config: AppConfig): void {
  app.use(helmet());
  app.enableShutdownHooks();

  // `/metrics` stays at the root for scrapers; everything else is /api/vN/...
  app.setGlobalPrefix(GLOBAL_PREFIX, { exclude: ['metrics'] });
  app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' });

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: { enableImplicitConversion: false },
    }),
  );

  if (config.NODE_ENV !== 'production') {
    const swaggerConfig = new DocumentBuilder()
      .setTitle(config.SERVICE_NAME)
      .setDescription('Golden service template API.')
      .setVersion('1.0')
      .build();
    const document = SwaggerModule.createDocument(app, swaggerConfig);
    SwaggerModule.setup(`${GLOBAL_PREFIX}/docs`, app, document);
  }
}

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule, { bufferLogs: true });
  const config = app.get<AppConfig>(APP_CONFIG);
  const logger = createLogger({
    service: config.SERVICE_NAME,
    level: config.LOG_LEVEL,
  });

  configureApp(app, config);

  await app.listen(config.PORT);
  logger.info(
    { port: config.PORT, env: config.NODE_ENV },
    `${config.SERVICE_NAME} listening on port ${config.PORT}`,
  );
}

// istanbul ignore next -- bootstrap side effect, exercised via e2e
if (require.main === module) {
  void bootstrap();
}
