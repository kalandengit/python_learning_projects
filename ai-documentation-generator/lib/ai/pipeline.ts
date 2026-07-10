import { OpenAiDocumentationProvider } from "@/lib/ai/providers/openai";
import type { GenerateFromImageResult } from "@/lib/ai/providers/types";

export type DocumentationPipelineInput = {
  imageUrl: string;
  userContext?: string;
};

export async function runDocumentationPipeline(input: DocumentationPipelineInput): Promise<GenerateFromImageResult> {
  const provider = new OpenAiDocumentationProvider();
  return provider.generateFromImage(input);
}
