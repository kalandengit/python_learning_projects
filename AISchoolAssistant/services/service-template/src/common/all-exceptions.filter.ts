import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
  Logger,
} from '@nestjs/common';
import type { Request, Response } from 'express';
import { AppError, InternalError, isAppError } from '@asa/errors';
import type { Problem } from '@asa/contracts';

/**
 * Global exception filter that renders every error as an RFC 9457
 * `application/problem+json` document. Domain errors ({@link AppError})
 * carry their own status/code/title; Nest {@link HttpException}s are mapped
 * to an equivalent problem; anything else becomes an opaque 500 so we never
 * leak internal details to clients.
 */
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  private readonly logger = new Logger(AllExceptionsFilter.name);

  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const appError = this.toAppError(exception);
    const problem = appError.toProblem(request.originalUrl);

    if (appError.status >= 500) {
      this.logger.error(
        `${request.method} ${request.originalUrl} -> ${appError.status} ${appError.code}`,
        exception instanceof Error ? exception.stack : String(exception),
      );
    } else {
      this.logger.warn(
        `${request.method} ${request.originalUrl} -> ${appError.status} ${appError.code}`,
      );
    }

    this.send(response, appError.status, problem);
  }

  private toAppError(exception: unknown): AppError {
    if (isAppError(exception)) {
      return exception;
    }

    if (exception instanceof HttpException) {
      return this.fromHttpException(exception);
    }

    return new InternalError();
  }

  private fromHttpException(exception: HttpException): AppError {
    const status = exception.getStatus();
    const payload = exception.getResponse();

    let detail: string | undefined;
    let errors: AppError['errors'];

    if (typeof payload === 'string') {
      detail = payload;
    } else if (payload && typeof payload === 'object') {
      const body = payload as Record<string, unknown>;
      const message = body.message;
      if (Array.isArray(message)) {
        detail = 'Request validation failed.';
        errors = message.map((m) => ({ field: '(body)', message: String(m) }));
      } else if (typeof message === 'string') {
        detail = message;
      }
    }

    return new HttpBackedError(status, exception.name, detail, errors);
  }

  private send(response: Response, status: number, problem: Problem): void {
    if (response.headersSent) {
      return;
    }
    response.status(status).type('application/problem+json').json(problem);
  }
}

/**
 * Adapter that lets a Nest {@link HttpException} flow through the same
 * {@link AppError#toProblem} rendering path as domain errors.
 */
class HttpBackedError extends AppError {
  constructor(
    status: number,
    name: string,
    detail?: string,
    errors?: AppError['errors'],
  ) {
    const code = name
      .replace(/Exception$/, '')
      .replace(/([a-z])([A-Z])/g, '$1_$2')
      .toUpperCase();
    super({
      status,
      code: code || 'HTTP_ERROR',
      title: name,
      detail,
      errors,
    });
  }
}
