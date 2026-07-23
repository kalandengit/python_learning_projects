/** Ambient context for an agent run (who/where), used for tools + audit. */
export interface AgentContext {
  tenantId?: string;
  /** Principal subject initiating the run. */
  actor?: string;
  correlationId?: string;
}

/** Sensitivity of the data an agent handles. */
export type DataClassification =
  'public' | 'internal' | 'confidential' | 'restricted';

/** Governance metadata every agent declares (audited on each run). */
export interface AgentGovernance {
  owner: string;
  dataClassification: DataClassification;
  pii: boolean;
  /** Concrete `provider:model` references the agent is permitted to use. */
  modelAllowList: string[];
  tags?: string[];
}
