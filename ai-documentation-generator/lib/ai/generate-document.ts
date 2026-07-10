import type { GeneratedDocument } from "@/lib/ai/schemas";
import { runDocumentationPipeline } from "@/lib/ai/pipeline";

export async function generateDocumentationFromImageUrl(imageUrl: string, userContext?: string): Promise<GeneratedDocument> {
  const result = await runDocumentationPipeline({ imageUrl, userContext });
  return result.document;
}

export async function generateDocumentationFromImage(params: { imageUrl: string; userContext?: string }) {
  return generateDocumentationFromImageUrl(params.imageUrl, params.userContext);
}
