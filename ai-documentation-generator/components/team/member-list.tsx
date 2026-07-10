import { removeMemberAction, updateMemberRoleAction } from "@/app/(dashboard)/actions";
import { Button } from "@/components/ui/button";
import type { OrganizationMember, Role } from "@/lib/types";

export function MemberList({ members, currentUserId, canManage }: { members: OrganizationMember[]; currentUserId: string; canManage: boolean }) {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold">Members</h2>
      <div className="mt-4 overflow-hidden rounded-xl border">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="px-4 py-3">User ID</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Joined</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {members.map((member) => {
              const isSelf = member.user_id === currentUserId;
              const isOwner = member.role === "owner";
              return (
                <tr key={member.user_id}>
                  <td className="px-4 py-3 font-mono text-xs">{member.user_id}{isSelf ? " (you)" : ""}</td>
                  <td className="px-4 py-3">
                    {canManage && !isOwner ? (
                      <form action={updateMemberRoleAction} className="flex gap-2">
                        <input type="hidden" name="organization_id" value={member.organization_id} />
                        <input type="hidden" name="user_id" value={member.user_id} />
                        <select name="role" defaultValue={member.role} className="rounded-lg border px-2 py-1 text-xs">
                          <option value="member">Member</option>
                          <option value="admin">Admin</option>
                        </select>
                        <Button type="submit" variant="secondary">Update</Button>
                      </form>
                    ) : (
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium capitalize">{member.role}</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-500">{member.joined_at ? new Date(member.joined_at).toLocaleDateString() : "—"}</td>
                  <td className="px-4 py-3 text-right">
                    {canManage && !isOwner && !isSelf ? (
                      <form action={removeMemberAction}>
                        <input type="hidden" name="organization_id" value={member.organization_id} />
                        <input type="hidden" name="user_id" value={member.user_id} />
                        <Button type="submit" variant="secondary">Remove</Button>
                      </form>
                    ) : <span className="text-xs text-slate-400">—</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
