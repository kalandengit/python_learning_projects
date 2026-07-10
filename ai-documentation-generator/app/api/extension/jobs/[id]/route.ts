import { authenticateExtensionRequest, extensionErrorResponse } from "@/lib/extension/tokens";
import { createAdminClient } from "@/lib/supabase/admin";
export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const principal = await authenticateExtensionRequest(request, "jobs:read");
    const { id } = await context.params;
    const { data, error } = await createAdminClient().from("ai_jobs")
      .select("id,status,document_id,error_message,created_at,started_at,completed_at")
      .eq("id", id).eq("organization_id", principal.organizationId).single();
    if (error) return Response.json({ error: "Job not found." }, { status: 404 });
    return Response.json({ job: data });
  } catch (error) { return extensionErrorResponse(error); }
}
