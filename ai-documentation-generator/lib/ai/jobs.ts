import type { SupabaseClient } from "@supabase/supabase-js";
import { runDocumentationPipeline } from "@/lib/ai/pipeline";
import { generatedDocumentToMarkdown } from "@/lib/markdown";
import { slugify } from "@/lib/slug";
import { nanoid } from "nanoid";

export async function createAiJob(supabase: SupabaseClient, params: {
  organizationId: string;
  userId: string;
  uploadId: string;
}) {
  const { data, error } = await supabase
    .from("ai_jobs")
    .insert({
      organization_id: params.organizationId,
      upload_id: params.uploadId,
      user_id: params.userId,
      job_type: "document_generation",
      status: "queued",
      provider: "openai",
      max_attempts: Number(process.env.AI_JOB_MAX_ATTEMPTS ?? 3)
    })
    .select("id")
    .single();
  if (error) throw error;
  return data.id as string;
}

export async function processDocumentationJob(supabase: SupabaseClient, params: {
  jobId: string;
  upload: any;
  signedUrl: string;
  userId: string;
}) {
  await supabase.from("ai_jobs").update({
    status: "processing",
    started_at: new Date().toISOString()
  }).eq("id", params.jobId);

  try {
    const result = await runDocumentationPipeline({ imageUrl: params.signedUrl });
    const markdown = generatedDocumentToMarkdown(result.document);
    const slug = `${slugify(result.document.title)}-${nanoid(6)}`;

    const { data: doc, error: docError } = await supabase
      .from("documents")
      .insert({
        organization_id: params.upload.organization_id,
        project_id: params.upload.project_id,
        upload_id: params.upload.id,
        title: result.document.title,
        slug,
        content_json: result.document,
        content_markdown: markdown,
        visibility: "private",
        created_by: params.userId
      })
      .select("id")
      .single();
    if (docError) throw docError;

    await supabase.from("ai_jobs").update({
      status: "completed",
      document_id: doc.id,
      model: result.rawModel,
      input_tokens: result.usage.inputTokens,
      output_tokens: result.usage.outputTokens,
      total_tokens: result.usage.totalTokens,
      estimated_cost_usd: result.usage.estimatedCostUsd,
      completed_at: new Date().toISOString()
    }).eq("id", params.jobId);

    await supabase.from("usage_events").insert({
      organization_id: params.upload.organization_id,
      user_id: params.userId,
      event_type: "document.generated",
      metadata: {
        upload_id: params.upload.id,
        document_id: doc.id,
        job_id: params.jobId,
        provider: result.provider,
        model: result.rawModel,
        tokens: result.usage.totalTokens,
        estimated_cost_usd: result.usage.estimatedCostUsd
      }
    });

    return doc.id as string;
  } catch (error) {
    await supabase.from("ai_jobs").update({
      status: "failed",
      error_message: error instanceof Error ? error.message : "AI job failed",
      completed_at: new Date().toISOString()
    }).eq("id", params.jobId);
    throw error;
  }
}
