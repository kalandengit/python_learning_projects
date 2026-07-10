import { authenticateExtensionRequest, extensionErrorResponse } from "@/lib/extension/tokens";
import { createAdminClient } from "@/lib/supabase/admin";
export async function GET(request: Request) {
  try {
    const principal = await authenticateExtensionRequest(request);
    const admin = createAdminClient();
    const [{ data: profile }, { data: organization }] = await Promise.all([
      admin.from("profiles").select("full_name,avatar_url").eq("id", principal.userId).maybeSingle(),
      admin.from("organizations").select("id,name").eq("id", principal.organizationId).single()
    ]);
    return Response.json({ user: { id: principal.userId, fullName: profile?.full_name ?? null }, organization });
  } catch (error) { return extensionErrorResponse(error); }
}
