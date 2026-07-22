import type { Problem, ProblemError } from '@asa/contracts';

/**
 * Base class for all expected application errors. Carries an HTTP status, a
 * stable machine `code`, and renders to RFC 9457 problem+json. Feature code
 * throws these; the HTTP layer serializes them uniformly.
 */
export class AppError extends Error {
  readonly status: number;
  readonly code: string;
  readonly title: string;
  readonly detail?: string;
  readonly errors?: ProblemError[];

  constructor(params: {
    status: number;
    code: string;
    title: string;
    detail?: string;
    errors?: ProblemError[];
  }) {
    super(params.detail ?? params.title);
    this.name = new.target.name;
    this.status = params.status;
    this.code = params.code;
    this.title = params.title;
    this.detail = params.detail;
    this.errors = params.errors;
    // V8-only API; guard so the library stays runtime-agnostic and buildable
    // without @types/node.
    const captureStackTrace = (
      Error as unknown as {
        captureStackTrace?: (target: object, ctor?: unknown) => void;
      }
    ).captureStackTrace;
    captureStackTrace?.(this, new.target);
  }

  /** Render as a problem+json body. `instance` is the request path, if known. */
  toProblem(instance?: string): Problem {
    return {
      type: `urn:asa:error:${this.code}`,
      title: this.title,
      status: this.status,
      detail: this.detail,
      instance,
      errors: this.errors,
    };
  }
}

export class ValidationError extends AppError {
  constructor(detail = 'Validation failed.', errors?: ProblemError[]) {
    super({
      status: 400,
      code: 'validation_error',
      title: 'Bad Request',
      detail,
      errors,
    });
  }
}

export class UnauthorizedError extends AppError {
  constructor(detail = 'Authentication required.') {
    super({ status: 401, code: 'unauthorized', title: 'Unauthorized', detail });
  }
}

export class ForbiddenError extends AppError {
  constructor(detail = 'Insufficient permissions.') {
    super({ status: 403, code: 'forbidden', title: 'Forbidden', detail });
  }
}

export class NotFoundError extends AppError {
  constructor(detail = 'Resource not found.') {
    super({ status: 404, code: 'not_found', title: 'Not Found', detail });
  }
}

export class ConflictError extends AppError {
  constructor(detail = 'Resource conflict.') {
    super({ status: 409, code: 'conflict', title: 'Conflict', detail });
  }
}

export class TooManyRequestsError extends AppError {
  constructor(detail = 'Rate limit exceeded.') {
    super({
      status: 429,
      code: 'too_many_requests',
      title: 'Too Many Requests',
      detail,
    });
  }
}

export class InternalError extends AppError {
  constructor(detail = 'An unexpected error occurred.') {
    super({
      status: 500,
      code: 'internal_error',
      title: 'Internal Server Error',
      detail,
    });
  }
}

/** Type guard. */
export function isAppError(err: unknown): err is AppError {
  return err instanceof AppError;
}
