import { requireUser } from "@/lib/auth/session";
import type { Role } from "@/lib/types";

const ROLE_RANK: Record<Role, number> = { member: 1, admin: 2, owner: 3 };

/** Returns true when a role has at least the requested privilege. */
export function hasRoleAtLeast(role: Role | null | undefined, minimum: Role) {
  if (!role) return false;
  return ROLE_RANK[role] >= ROLE_RANK[minimum];
}

/** Loads the current user's role for an organization using RLS-safe membership data. */
export async function getCurrentUserOrgRole(organizationId: string): Promise<Role | null> {
  const { supabase, user } = await requireUser();
  const { data, error } = await supabase
    .from("organization_members")
    .select("role")
    .eq("organization_id", organizationId)
    .eq("user_id", user.id)
    .maybeSingle();
  if (error) throw error;
  return (data?.role as Role | undefined) ?? null;
}

/** Throws a clear error when the user cannot perform an organization action. */
export async function requireOrgRole(organizationId: string, minimum: Role) {
  const role = await getCurrentUserOrgRole(organizationId);
  if (!hasRoleAtLeast(role, minimum)) {
    throw new Error(`You need ${minimum} access or higher to perform this action.`);
  }
  return role;
}
