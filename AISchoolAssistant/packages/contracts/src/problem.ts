/**
 * RFC 9457 "Problem Details for HTTP APIs" — the platform-wide error envelope.
 * Every service returns errors in this shape.
 */
export interface ProblemError {
  field?: string;
  message: string;
}

export interface Problem {
  /** A URI reference identifying the problem type. */
  type: string;
  /** Short, human-readable summary of the problem type. */
  title: string;
  /** HTTP status code. */
  status: number;
  /** Human-readable explanation specific to this occurrence. */
  detail?: string;
  /** URI reference identifying the specific occurrence. */
  instance?: string;
  /** Field-level validation errors, when applicable. */
  errors?: ProblemError[];
}
