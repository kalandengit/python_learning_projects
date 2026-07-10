import { z } from "zod";

export const documentationStepSchema = z.object({
  order: z.number().int().positive(),
  title: z.string().min(3),
  instruction: z.string().min(10),
  expected_result: z.string().min(5),
  ui_elements: z.array(z.string()).default([]),
  tip: z.string().nullable().optional()
});

export const documentationFaqSchema = z.object({
  question: z.string().min(5),
  answer: z.string().min(10)
});

export const generatedDocumentSchema = z.object({
  title: z.string().min(3),
  summary: z.string().min(20),
  audience: z.enum(["end_user", "support", "internal_team", "technical_writer", "qa", "admin"]).default("end_user"),
  document_type: z.enum(["user_guide", "sop", "help_article", "qa_test_case", "training_guide"]).default("help_article"),
  confidence_score: z.number().min(0).max(1),
  detected_ui: z.object({
    app_or_page_name: z.string().nullable().optional(),
    primary_goal: z.string().nullable().optional(),
    visible_elements: z.array(z.string()).default([]),
    forms: z.array(z.string()).default([]),
    buttons: z.array(z.string()).default([]),
    navigation_items: z.array(z.string()).default([])
  }),
  steps: z.array(documentationStepSchema).min(1),
  warnings: z.array(z.string()).default([]),
  tips: z.array(z.string()).default([]),
  faq: z.array(documentationFaqSchema).default([]),
  metadata: z.object({
    language: z.string().default("en"),
    generated_at: z.string(),
    model: z.string(),
    provider: z.string()
  })
});

export type GeneratedDocument = z.infer<typeof generatedDocumentSchema>;

export const generatedDocumentJsonSchema = {
  name: "generated_document",
  strict: true,
  schema: {
    type: "object",
    additionalProperties: false,
    required: ["title", "summary", "audience", "document_type", "confidence_score", "detected_ui", "steps", "warnings", "tips", "faq", "metadata"],
    properties: {
      title: { type: "string", minLength: 3 },
      summary: { type: "string", minLength: 20 },
      audience: { type: "string", enum: ["end_user", "support", "internal_team", "technical_writer", "qa", "admin"] },
      document_type: { type: "string", enum: ["user_guide", "sop", "help_article", "qa_test_case", "training_guide"] },
      confidence_score: { type: "number", minimum: 0, maximum: 1 },
      detected_ui: {
        type: "object",
        additionalProperties: false,
        required: ["app_or_page_name", "primary_goal", "visible_elements", "forms", "buttons", "navigation_items"],
        properties: {
          app_or_page_name: { type: ["string", "null"] },
          primary_goal: { type: ["string", "null"] },
          visible_elements: { type: "array", items: { type: "string" } },
          forms: { type: "array", items: { type: "string" } },
          buttons: { type: "array", items: { type: "string" } },
          navigation_items: { type: "array", items: { type: "string" } }
        }
      },
      steps: {
        type: "array",
        minItems: 1,
        items: {
          type: "object",
          additionalProperties: false,
          required: ["order", "title", "instruction", "expected_result", "ui_elements", "tip"],
          properties: {
            order: { type: "integer", minimum: 1 },
            title: { type: "string" },
            instruction: { type: "string" },
            expected_result: { type: "string" },
            ui_elements: { type: "array", items: { type: "string" } },
            tip: { type: ["string", "null"] }
          }
        }
      },
      warnings: { type: "array", items: { type: "string" } },
      tips: { type: "array", items: { type: "string" } },
      faq: {
        type: "array",
        items: {
          type: "object",
          additionalProperties: false,
          required: ["question", "answer"],
          properties: {
            question: { type: "string" },
            answer: { type: "string" }
          }
        }
      },
      metadata: {
        type: "object",
        additionalProperties: false,
        required: ["language", "generated_at", "model", "provider"],
        properties: {
          language: { type: "string" },
          generated_at: { type: "string" },
          model: { type: "string" },
          provider: { type: "string" }
        }
      }
    }
  }
} as const;
