export {
  type VectorStore,
  type VectorRecord,
  type VectorMatch,
  type VectorQuery,
  InMemoryVectorStore,
  cosineSimilarity,
} from './vector-store';
export {
  KnowledgeService,
  type KnowledgeServiceDeps,
  type KnowledgeDocument,
  type KnowledgeHit,
  type KnowledgeSearchOptions,
} from './knowledge-service';
export {
  KnowledgeModule,
  type KnowledgeModuleOptions,
} from './nest/knowledge.module';
export { VECTOR_STORE, EMBEDDING_PROVIDER } from './nest/tokens';
