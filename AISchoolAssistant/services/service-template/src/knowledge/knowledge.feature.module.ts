import { Module } from '@nestjs/common';
import { KnowledgeController } from './knowledge.controller';

/**
 * Feature module exposing the knowledge endpoints. The platform itself
 * (embedding provider, vector store, service) is provided globally by
 * `KnowledgeModule.forRoot` in the app module; this module wires the HTTP
 * surface only.
 */
@Module({
  controllers: [KnowledgeController],
})
export class KnowledgeFeatureModule {}
