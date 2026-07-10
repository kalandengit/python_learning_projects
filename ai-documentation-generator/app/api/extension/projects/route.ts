import { authenticateExtensionRequest, extensionErrorResponse } from "@/lib/extension/tokens";
import { createAdminClient } from "@/lib/supabase/admin";
export async function GET(request: Request) {
  try {
    const principal = await authenticateExtensionRequest(request, "projects:read");
    const { data, error } = await createAdminClient().from("projects").select("id,name,description")
      .eq("organization_id", principal.organizationId).order("created_at", { ascending: false });
    if (error) throw error;
    return Response.json({ projects: data ?? [] });
  } catch (error) { return extensionErrorResponse(error); }
}
