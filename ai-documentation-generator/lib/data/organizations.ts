import { requireUser } from "@/lib/auth/session";
import type { Organization } from "@/lib/types";

/** Returns the user's active organization. For MVP we auto-create one if missing. */
export async function getOrCreateDefaultOrganization(): Promise<Organization> {
  const { supabase, user } = await requireUser();
  const { data: existing, error: selectError } = await supabase
    .from("organizations")
    .select("*")
    .order("created_at", { ascending: true })
    .limit(1)
    .maybeSingle();
  if (selectError) throw selectError;
  if (existing) return existing as Organization;

  const displayName = user.user_metadata?.full_name || user.email?.split("@")[0] || "My";
  const { data: org, error: orgError } = await supabase
    .from("organizations")
    .insert({ name: `${displayName}'s Workspace`, owner_id: user.id })
    .select("*")
    .single();
  if (orgError) throw orgError;

  const { error: memberError } = await supabase
    .from("organization_members")
    .insert({ organization_id: org.id, user_id: user.id, role: "owner" });
  if (memberError) throw memberError;
  return org as Organization;
}
