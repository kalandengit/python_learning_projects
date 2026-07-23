/** Role of a chat message, aligned with the common provider conventions. */
export type ChatRole = 'system' | 'user' | 'assistant' | 'tool';

/** A single message in a chat conversation. */
export interface ChatMessage {
  role: ChatRole;
  content: string;
  /** Optional author name / tool name. */
  name?: string;
  /** Correlates a `tool` message with the assistant tool call it answers. */
  toolCallId?: string;
  /** Tool calls emitted by an assistant turn, preserved in history. */
  toolCalls?: ToolCall[];
}

/** A tool the model may call, described with a JSON Schema parameter object. */
export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

/** A tool invocation requested by the model. */
export interface ToolCall {
  id: string;
  name: string;
  /** Raw JSON arguments string, as emitted by the model. */
  arguments: string;
}

/** Why generation stopped. */
export type FinishReason =
  'stop' | 'length' | 'tool_calls' | 'content_filter' | 'error';

/** Token accounting for a request (provider-reported or estimated). */
export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

/** A provider-agnostic chat completion request. */
export interface ChatRequest {
  /** Logical model reference (`provider:model`) or a routing alias. */
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  maxTokens?: number;
  tools?: ToolDefinition[];
  /** Hint that the caller expects a JSON object as the response body. */
  responseFormat?: 'text' | 'json';
  /** Opaque, provider-agnostic passthrough metadata. */
  metadata?: Record<string, unknown>;
}

/** A completed chat generation. */
export interface ChatResult {
  text: string;
  finishReason: FinishReason;
  usage: TokenUsage;
  toolCalls?: ToolCall[];
  /** The concrete model that produced the result. */
  model: string;
  /** Provider-native raw payload, when retained for debugging. */
  raw?: unknown;
}

/** An incremental streaming delta. */
export interface ChatChunk {
  delta: string;
  finishReason?: FinishReason;
}

/** A provider-agnostic embedding request. */
export interface EmbeddingRequest {
  model: string;
  input: string[];
}

/** Embedding vectors for the requested inputs. */
export interface EmbeddingResult {
  model: string;
  embeddings: number[][];
  usage: TokenUsage;
}
