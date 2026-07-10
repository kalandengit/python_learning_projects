import type { SupabaseClient } from "@supabase/supabase-js";
import { captureEvent } from "@/lib/analytics/events";

export type ExportFormat = "markdown" | "html" | "pdf";
export type ExportStatus = "created" | "failed";

/**
 * Records exports for auditability, future billing, and customer analytics.
 * Export generation is a user-visible value metric, so track it from Sprint 06.
 */
export async function recordExport(
  supabase: SupabaseClient,
  input: {
    organizationId: string;
    documentId: string;
    userId?: string | null;
    format: ExportFormat;
    status: ExportStatus;
    fileName?: string | null;
    errorMessage?: string | null;
  }
) {
  await supabase.from("exports").insert({
    organization_id: input.organizationId,
    document_id: input.documentId,
    user_id: input.userId ?? null,
    format: input.format,
    status: input.status,
    file_name: input.fileName ?? null,
    error_message: input.errorMessage ?? null
  });

  if (input.status === "created") {
    await captureEvent({
      organizationId: input.organizationId,
      userId: input.userId ?? null,
      eventName: "export_created",
      properties: { document_id: input.documentId, format: input.format }
    });
  }
}
