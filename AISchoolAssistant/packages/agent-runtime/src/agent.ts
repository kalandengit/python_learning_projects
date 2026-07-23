import { ConflictError, NotFoundError } from '@asa/errors';
import type { AgentGovernance } from './context';

/**
 * An **agent**: a named, versioned unit that pursues a goal by reasoning with a
 * model and calling registered tools, bounded by `maxSteps`. Governance
 * declares the models it may use and who owns it.
 */
export interface AgentDefinition {
  id: string;
  version: string;
  description: string;
  /** System instructions that define the agent's behavior and boundaries. */
  instructions: string;
  /** Logical model reference or routing alias. */
  model: string;
  /** Names of tools (from the ToolRegistry) this agent may call. */
  tools: string[];
  /** Hard cap on reasoning/tool iterations (prevents runaway loops). */
  maxSteps: number;
  temperature?: number;
  governance: AgentGovernance;
}

/** The catalog of registered agents, keyed by id + version. */
export class AgentRegistry {
  private readonly agents = new Map<string, AgentDefinition>();

  constructor(agents: AgentDefinition[] = []) {
    for (const agent of agents) {
      this.register(agent);
    }
  }

  register(agent: AgentDefinition): void {
    const key = `${agent.id}@${agent.version}`;
    if (this.agents.has(key)) {
      throw new ConflictError(`Agent "${key}" is already registered.`);
    }
    if (agent.maxSteps < 1) {
      throw new ConflictError(`Agent "${key}" must allow at least one step.`);
    }
    this.agents.set(key, agent);
  }

  get(id: string, version: string): AgentDefinition {
    const agent = this.agents.get(`${id}@${version}`);
    if (!agent) {
      throw new NotFoundError(`Agent "${id}@${version}" is not registered.`);
    }
    return agent;
  }

  has(id: string, version: string): boolean {
    return this.agents.has(`${id}@${version}`);
  }

  list(): Array<{ id: string; version: string }> {
    return [...this.agents.values()].map((a) => ({
      id: a.id,
      version: a.version,
    }));
  }
}
