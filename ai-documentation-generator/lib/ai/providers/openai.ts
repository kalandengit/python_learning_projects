import OpenAI from "openai";
import { generatedDocumentJsonSchema, generatedDocumentSchema } from "@/lib/ai/schemas";
import { buildDocumentationUserPrompt, DOCUMENTATION_SYSTEM_PROMPT } from "@/lib/ai/prompts/documentation";
import type { AiDocumentationProvider, GenerateFromImageInput, GenerateFromImageResult } from "@/lib/ai/providers/types";

const DEFAULT_MODEL = process.env.OPENAI_VISION_MODEL || "gpt-4o-mini";

function estimateOpenAiCostUsd(model: string, inputTokens: number, outputTokens: number) {
  // Conservative placeholder cost tracking. Replace with exact pricing in production billing code.
  // gpt-4o-mini historical public pricing has been low; this keeps usage telemetry useful in MVP.
  const lower = model.toLowerCase();
  const inputPerMillion = lower.includes("mini") ? 0.15 : 5;
  const outputPerMillion = lower.includes("mini") ? 0.6 : 15;
  return (inputTokens / 1_000_000) * inputPerMillion + (outputTokens / 1_000_000) * outputPerMillion;
}

export class OpenAiDocumentationProvider implements AiDocumentationProvider {
  name = "openai" as const;
  private client: OpenAI;

  constructor(apiKey = process.env.OPENAI_API_KEY) {
    if (!apiKey) throw new Error("Missing OPENAI_API_KEY");
    this.client = new OpenAI({ apiKey });
  }

  async generateFromImage(input: GenerateFromImageInput): Promise<GenerateFromImageResult> {
    const model = input.model || DEFAULT_MODEL;
    const completion = await this.client.chat.completions.create({
      model,
      temperature: 0.2,
      response_format: {
        type: "json_schema",
        json_schema: generatedDocumentJsonSchema
      },
      messages: [
        { role: "system", content: DOCUMENTATION_SYSTEM_PROMPT },
        {
          role: "user",
          content: [
            { type: "text", text: buildDocumentationUserPrompt(input.userContext) },
            { type: "image_url", image_url: { url: input.imageUrl, detail: "high" } }
          ]
        }
      ]
    });

    const content = completion.choices[0]?.message?.content;
    if (!content) throw new Error("OpenAI returned an empty response.");

    const parsed = generatedDocumentSchema.parse(JSON.parse(content));
    const inputTokens = completion.usage?.prompt_tokens ?? 0;
    const outputTokens = completion.usage?.completion_tokens ?? 0;
    const totalTokens = completion.usage?.total_tokens ?? inputTokens + outputTokens;

    return {
      document: {
        ...parsed,
        metadata: {
          ...parsed.metadata,
          model,
          provider: this.name,
          generated_at: parsed.metadata.generated_at || new Date().toISOString()
        }
      },
      usage: {
        inputTokens,
        outputTokens,
        totalTokens,
        estimatedCostUsd: estimateOpenAiCostUsd(model, inputTokens, outputTokens)
      },
      rawModel: model,
      provider: this.name
    };
  }
}
