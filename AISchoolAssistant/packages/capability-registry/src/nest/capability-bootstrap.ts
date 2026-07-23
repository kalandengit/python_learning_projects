import {
  Inject,
  Injectable,
  Logger,
  type OnApplicationBootstrap,
} from '@nestjs/common';
import { AiProviderRegistry, ModelRouter } from '@asa/ai-sdk';
/* eslint-disable @typescript-eslint/no-explicit-any */
import type { CapabilityDefinition } from '../capability';
import { CapabilityRegistry } from '../capability-registry';
import {
  AI_CAPABILITIES,
  AI_PROVIDER_REGISTRY,
  CAPABILITY_REGISTRY,
  MODEL_ROUTER,
} from './tokens';

/**
 * Registers and evaluates each configured capability at application boot,
 * publishing only those whose evaluation passes. A failing evaluation aborts
 * startup (fail-fast) — a service never comes up serving an un-evaluated or
 * regressed capability.
 */
@Injectable()
export class CapabilityBootstrap implements OnApplicationBootstrap {
  private readonly logger = new Logger(CapabilityBootstrap.name);

  constructor(
    @Inject(CAPABILITY_REGISTRY) private readonly registry: CapabilityRegistry,
    @Inject(AI_PROVIDER_REGISTRY)
    private readonly providers: AiProviderRegistry,
    @Inject(MODEL_ROUTER) private readonly router: ModelRouter,
    @Inject(AI_CAPABILITIES)
    private readonly capabilities: CapabilityDefinition<any, any>[],
  ) {}

  async onApplicationBootstrap(): Promise<void> {
    const deps = { providers: this.providers, router: this.router };
    for (const capability of this.capabilities) {
      const report = await this.registry.registerAndPublish(capability, deps);
      this.logger.log(
        `Published capability ${capability.id}@${capability.version} ` +
          `(eval ${report.passed}/${report.total}, passRate ${report.passRate.toFixed(2)}).`,
      );
    }
  }
}
