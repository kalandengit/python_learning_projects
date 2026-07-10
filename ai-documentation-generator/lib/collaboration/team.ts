import { createClient } from "@/lib/supabase/server";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";
import type { OrganizationMember, OrganizationInvitation } from "@/lib/types";

export async function getTeamPageData() {
  const supabase = await createClient();
  const organization = await getOrCreateDefaultOrganization();

  const { data: members, error: membersError } = await supabase
    .from("organization_members")
    .select("organization_id, user_id, role, invited_by, joined_at, created_at")
    .eq("organization_id", organization.id)
    .order("created_at", { ascending: true });
  if (membersError) throw membersError;

  const { data: invitations, error: invitationsError } = await supabase
    .from("organization_invitations")
    .select("*")
    .eq("organization_id", organization.id)
    .is("accepted_at", null)
    .order("created_at", { ascending: false });
  if (invitationsError) throw invitationsError;

  return {
    organization,
    members: (members ?? []) as OrganizationMember[],
    invitations: (invitations ?? []) as OrganizationInvitation[]
  };
}
