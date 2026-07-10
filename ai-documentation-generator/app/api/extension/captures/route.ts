import { nanoid } from "nanoid";
import { z } from "zod";
import { authenticateExtensionRequest, extensionErrorResponse } from "@/lib/extension/tokens";
import { createAdminClient } from "@/lib/supabase/admin";
import { assertQuotaAvailable, recordUsageEvent } from "@/lib/billing/usage";
import { createAiJob } from "@/lib/ai/jobs";
import { enqueueAiDocumentationJob } from "@/lib/jobs/ai-documentation-queue";

const metadataSchema = z.object({ projectId: z.string().uuid().nullable().optional(), pageUrl: z.string().url().max(4000), pageTitle: z.string().max(500).optional(), captureMode: z.enum(["visible", "region", "full_page"]).default("visible") });
export async function POST(request: Request) {
  try {
    const principal = await authenticateExtensionRequest(request, "capture:write");
    const form = await request.formData();
    const file = form.get("file");
    const parsed = metadataSchema.safeParse({ projectId: form.get("projectId") || null, pageUrl: form.get("pageUrl"), pageTitle: form.get("pageTitle") || undefined, captureMode: form.get("captureMode") || "visible" });
    if (!parsed.success) return Response.json({ error: parsed.error.issues[0]?.message }, { status: 400 });
    if (!(file instanceof File) || !file.type.startsWith("image/") || file.size === 0) return Response.json({ error: "A valid image capture is required." }, { status: 400 });
    if (file.size > 12 * 1024 * 1024) return Response.json({ error: "Capture exceeds the 12MB extension limit." }, { status: 413 });

    const admin = createAdminClient();
    await assertQuotaAvailable(admin, principal.organizationId, "upload");
    await assertQuotaAvailable(admin, principal.organizationId, "document_generation");
    if (parsed.data.projectId) {
      const { data: project } = await admin.from("projects").select("id").eq("id", parsed.data.projectId).eq("organization_id", principal.organizationId).maybeSingle();
      if (!project) return Response.json({ error: "Project not found in this workspace." }, { status: 404 });
    }
    const storagePath = `${principal.organizationId}/${principal.userId}/extension-${Date.now()}-${nanoid(8)}.png`;
    const bytes = new Uint8Array(await file.arrayBuffer());
    const { error: storageError } = await admin.storage.from("uploads").upload(storagePath, bytes, { contentType: file.type, upsert: false });
    if (storageError) throw storageError;
    const { data: upload, error: uploadError } = await admin.from("uploads").insert({
      organization_id: principal.organizationId, project_id: parsed.data.projectId ?? null, user_id: principal.userId,
      storage_path: storagePath, file_name: file.name || "browser-capture.png", mime_type: file.type, size_bytes: file.size,
      status: "processing", source_url: parsed.data.pageUrl, source_title: parsed.data.pageTitle ?? null, capture_mode: parsed.data.captureMode
    }).select("id").single();
    if (uploadError) throw uploadError;
    await recordUsageEvent(admin, { organizationId: principal.organizationId, userId: principal.userId, eventType: "upload_created", metadata: { upload_id: upload.id, source: "browser_extension", capture_mode: parsed.data.captureMode } });
    const jobId = await createAiJob(admin, { organizationId: principal.organizationId, userId: principal.userId, uploadId: upload.id });
    const queued = await enqueueAiDocumentationJob({ jobId, uploadId: upload.id, userId: principal.userId, organizationId: principal.organizationId });
    await admin.from("ai_jobs").update({ queue_provider: queued.queued ? "bullmq" : "database", queue_job_id: queued.queued ? queued.bullJobId : null }).eq("id", jobId);
    return Response.json({ uploadId: upload.id, jobId, queued: queued.queued }, { status: 202 });
  } catch (error) { return extensionErrorResponse(error); }
}
