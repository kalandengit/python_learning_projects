import { requireUser } from "@/lib/auth/session";
import { getTeamPageData } from "@/lib/collaboration/team";
import { hasRoleAtLeast, getCurrentUserOrgRole } from "@/lib/collaboration/permissions";
import { InviteMemberForm } from "@/components/team/invite-member-form";
import { MemberList } from "@/components/team/member-list";
import { InvitationList } from "@/components/team/invitation-list";

export default async function TeamPage() {
  const { user } = await requireUser();
  const { organization, members, invitations } = await getTeamPageData();
  const currentRole = await getCurrentUserOrgRole(organization.id);
  const canInvite = hasRoleAtLeast(currentRole, "admin");
  const canManageMembers = hasRoleAtLeast(currentRole, "owner");

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium text-indigo-600">Sprint 09</p>
        <h1 className="text-3xl font-bold">Team & permissions</h1>
        <p className="mt-2 text-slate-600">Manage collaborators, pending invitations, and workspace access for {organization.name}.</p>
      </div>
      <InviteMemberForm organizationId={organization.id} disabled={!canInvite} />
      <MemberList members={members} currentUserId={user.id} canManage={canManageMembers} />
      <InvitationList invitations={invitations} canManage={canInvite} />
    </div>
  );
}
