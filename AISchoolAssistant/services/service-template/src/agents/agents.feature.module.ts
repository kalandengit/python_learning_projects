import { Module } from '@nestjs/common';
import { AgentsController } from './agents.controller';

/**
 * Feature module exposing the agent endpoints. The runtime itself (executor,
 * registries, providers) is provided globally by `AgentModule.forRoot` in the
 * app module; this module only wires the HTTP surface.
 */
@Module({
  controllers: [AgentsController],
})
export class AgentsFeatureModule {}
