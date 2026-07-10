import type { GeneratedDocument } from "@/lib/ai/schemas";

export type AiProviderName = "openai";

export type GenerateFromImageInput = {
  imageUrl: string;
  userContext?: string;
  model?: string;
};

export type AiUsage = {
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  estimatedCostUsd: number;
};

export type GenerateFromImageResult = {
  document: GeneratedDocument;
  usage: AiUsage;
  rawModel: string;
  provider: AiProviderName;
};

export interface AiDocumentationProvider {
  name: AiProviderName;
  generateFromImage(input: GenerateFromImageInput): Promise<GenerateFromImageResult>;
}
