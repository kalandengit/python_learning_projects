import { Module } from '@nestjs/common';
import { AiController } from './ai.controller';

/**
 * Feature module exposing the AI capability endpoints. The AI runtime itself
 * (executor, registry, providers) is provided globally by `AiModule.forRoot`
 * in the app module; this module only wires the HTTP surface.
 */
@Module({
  controllers: [AiController],
})
export class AiFeatureModule {}
