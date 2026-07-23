import { ConflictError, NotFoundError } from '@asa/errors';
import type { ToolDefinition } from '@asa/ai-sdk';
import type { ZodType } from 'zod';
import type { AgentContext } from './context';

/**
 * A tool an agent may call. `parameters` is the JSON Schema advertised to the
 * model; `inputSchema` (zod) validates the arguments the model returns before
 * `execute` runs — never trust model-produced arguments unchecked.
 */
export interface AgentTool<Args = unknown, Result = unknown> {
  name: string;
  description: string;
  /** JSON Schema for the model's function-calling interface. */
  parameters: Record<string, unknown>;
  /** Runtime validation of the model-produced arguments. */
  inputSchema: ZodType<Args>;
  execute(args: Args, context: AgentContext): Promise<Result> | Result;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
type AnyTool = AgentTool<any, any>;

/** Registry of tools available to agents, keyed by tool name. */
export class ToolRegistry {
  private readonly tools = new Map<string, AnyTool>();

  constructor(tools: AnyTool[] = []) {
    for (const tool of tools) {
      this.register(tool);
    }
  }

  register(tool: AnyTool): void {
    if (this.tools.has(tool.name)) {
      throw new ConflictError(`Tool "${tool.name}" is already registered.`);
    }
    this.tools.set(tool.name, tool);
  }

  get(name: string): AnyTool {
    const tool = this.tools.get(name);
    if (!tool) {
      throw new NotFoundError(`Tool "${name}" is not registered.`);
    }
    return tool;
  }

  has(name: string): boolean {
    return this.tools.has(name);
  }

  list(): string[] {
    return [...this.tools.keys()];
  }

  /** Build the model-facing tool definitions for the named tools. */
  toDefinitions(names: string[]): ToolDefinition[] {
    return names.map((name) => {
      const tool = this.get(name);
      return {
        name: tool.name,
        description: tool.description,
        parameters: tool.parameters,
      };
    });
  }
}
