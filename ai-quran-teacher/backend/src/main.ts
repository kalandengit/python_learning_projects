import { ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import helmet from 'helmet';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    // Trust the proxy so rate-limit client IPs and TLS info are accurate
    // behind a load balancer / ingress.
    bodyParser: true,
  });

  // Security headers.
  app.use(helmet());

  // CORS: lock down to configured origins in production.
  const origins = process.env.ALLOWED_ORIGINS?.split(',');
  app.enableCors({ origin: origins ?? true, credentials: true });

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidNonWhitelisted: true,
    }),
  );

  // Graceful shutdown so in-flight requests drain on SIGTERM (rolling deploys).
  app.enableShutdownHooks();

  const port = parseInt(process.env.PORT ?? '3000', 10);
  await app.listen(port, '0.0.0.0');
  console.log(`AI Quran Teacher backend running on port ${port}`);
}
bootstrap();
