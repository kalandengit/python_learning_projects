import type { SupabaseClient } from "@supabase/supabase-js";
import { processDocumentationJob } from "@/lib/ai/jobs";
import { recordUsageEvent } from "@/lib/billing/usage";
import { captureEvent } from "@/lib/analytics/events";

/**
 * Loads a queued AI job and processes it. This function is shared by the
 * BullMQ worker and the DB-drain fallback script so business logic lives in
 * one place.
 */
export async function runAiDocumentationJob(supabase: SupabaseClient, jobId: string) {
  const { data: job, error: jobError } = await supabase
    .from("ai_jobs")
    .select("*")
    .eq("id", jobId)
    .single();

  if (jobError || !job) throw jobError || new Error(`AI job ${jobId} not found.`);
  if (job.status === "completed") return { status: "already_completed", documentId: job.document_id };
  if (job.status === "cancelled") return { status: "cancelled" };
  if (!job.upload_id) throw new Error("AI job has no upload_id.");

  const { data: upload, error: uploadError } = await supabase
    .from("uploads")
    .select("*")
    .eq("id", job.upload_id)
    .single();

  if (uploadError || !upload) throw uploadError || new Error("Upload not found for AI job.");

  const { data: signed, error: signedError } = await supabase.storage
    .from("uploads")
    .createSignedUrl(upload.storage_path, 60 * 15);

  if (signedError || !signed?.signedUrl) throw signedError || new Error("Could not create signed URL for worker.");

  await supabase.from("ai_jobs").update({
    attempts: Number(job.attempts ?? 0) + 1,
    locked_at: new Date().toISOString(),
    locked_by: process.env.HOSTNAME ?? "worker"
  }).eq("id", jobId);

  const documentId = await processDocumentationJob(supabase, {
    jobId,
    upload,
    signedUrl: signed.signedUrl,
    userId: job.user_id
  });

  await supabase.from("uploads").update({ status: "completed", error_message: null }).eq("id", upload.id);
  await recordUsageEvent(supabase, {
    organizationId: job.organization_id,
    userId: job.user_id,
    eventType: "document_generated",
    metadata: { upload_id: upload.id, document_id: documentId, ai_job_id: jobId }
  });
  await captureEvent({
    organizationId: job.organization_id,
    userId: job.user_id,
    eventName: "document_created",
    source: "worker",
    properties: { upload_id: upload.id, document_id: documentId, ai_job_id: jobId }
  });
  return { status: "completed", documentId };
}
