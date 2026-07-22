import { describe, it, expect } from 'vitest';
import {
  AppError,
  NotFoundError,
  ValidationError,
  isAppError,
} from './app-error';

describe('AppError', () => {
  it('renders a NotFoundError as problem+json', () => {
    const problem = new NotFoundError('User 42 not found.').toProblem(
      '/users/42',
    );
    expect(problem).toEqual({
      type: 'urn:asa:error:not_found',
      title: 'Not Found',
      status: 404,
      detail: 'User 42 not found.',
      instance: '/users/42',
      errors: undefined,
    });
  });

  it('carries field errors on ValidationError', () => {
    const err = new ValidationError('Invalid body.', [
      { field: 'email', message: 'must be an email' },
    ]);
    expect(err.status).toBe(400);
    expect(err.toProblem().errors).toHaveLength(1);
  });

  it('is detected by the isAppError guard', () => {
    expect(isAppError(new NotFoundError())).toBe(true);
    expect(isAppError(new Error('plain'))).toBe(false);
  });

  it('sets name to the concrete subclass', () => {
    expect(new NotFoundError().name).toBe('NotFoundError');
    expect(
      new AppError({ status: 418, code: 'teapot', title: "I'm a teapot" }).name,
    ).toBe('AppError');
  });
});
