import { revokeInvitationAction } from "@/app/(dashboard)/actions";
import { Button } from "@/components/ui/button";
import type { OrganizationInvitation } from "@/lib/types";

export function InvitationList({ invitations, canManage }: { invitations: OrganizationInvitation[]; canManage: boolean }) {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold">Pending invitations</h2>
      {invitations.length === 0 ? (
        <p className="mt-3 text-sm text-slate-600">No pending invitations.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {invitations.map((invite) => (
            <div key={invite.id} className="flex items-center justify-between rounded-xl border p-4">
              <div>
                <p className="font-medium">{invite.email}</p>
                <p className="text-sm text-slate-500">Role: {invite.role} · Expires {new Date(invite.expires_at).toLocaleDateString()}</p>
                <p className="mt-1 break-all font-mono text-xs text-slate-400">/api/invitations/{invite.token}</p>
              </div>
              {canManage ? (
                <form action={revokeInvitationAction}>
                  <input type="hidden" name="organization_id" value={invite.organization_id} />
                  <input type="hidden" name="invitation_id" value={invite.id} />
                  <Button type="submit" variant="secondary">Revoke</Button>
                </form>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
