import { ValidationError } from '@asa/errors';

/** A logical model reference resolved to a concrete provider + model. */
export interface ResolvedModel {
  providerId: string;
  model: string;
  /** The concrete `provider:model` reference. */
  ref: string;
  /** The original alias/reference the caller supplied. */
  requested: string;
}

/**
 * Resolves logical model references to a concrete `provider:model`. References
 * may be:
 * - a concrete `provider:model` (e.g. `anthropic:claude-sonnet-5`), or
 * - a named **alias** mapped to a concrete reference (routing policy), or
 * - omitted, falling back to the configured default.
 *
 * Centralizing routing lets operators swap or re-route models (cost, latency,
 * availability) without touching feature or capability code.
 */
export class ModelRouter {
  constructor(
    private readonly aliases: Record<string, string> = {},
    private readonly defaultRef?: string,
  ) {}

  resolve(reference?: string): ResolvedModel {
    const requested = reference ?? this.defaultRef;
    if (!requested) {
      throw new ValidationError(
        'No model reference supplied and no default configured.',
      );
    }

    const resolved = this.aliases[requested] ?? requested;
    const separator = resolved.indexOf(':');
    if (separator <= 0 || separator === resolved.length - 1) {
      throw new ValidationError(
        `Model reference "${resolved}" must be of the form "provider:model".`,
      );
    }

    return {
      providerId: resolved.slice(0, separator),
      model: resolved.slice(separator + 1),
      ref: resolved,
      requested,
    };
  }
}
