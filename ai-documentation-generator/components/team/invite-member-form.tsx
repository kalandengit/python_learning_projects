import { inviteMemberAction } from "@/app/(dashboard)/actions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function InviteMemberForm({ organizationId, disabled }: { organizationId: string; disabled?: boolean }) {
  return (
    <form action={inviteMemberAction} className="rounded-2xl border bg-white p-5 shadow-sm">
      <input type="hidden" name="organization_id" value={organizationId} />
      <div className="mb-4">
        <h2 className="text-lg font-semibold">Invite teammate</h2>
        <p className="text-sm text-slate-600">Admins and owners can invite collaborators into this workspace.</p>
      </div>
      <div className="grid gap-3 md:grid-cols-[1fr_160px_auto]">
        <Input name="email" type="email" placeholder="teammate@company.com" required disabled={disabled} />
        <select name="role" defaultValue="member" disabled={disabled} className="rounded-xl border border-slate-200 px-3 py-2 text-sm">
          <option value="member">Member</option>
          <option value="admin">Admin</option>
        </select>
        <Button type="submit" disabled={disabled}>Send invite</Button>
      </div>
      {disabled ? <p className="mt-3 text-xs text-amber-600">You need admin or owner access to invite teammates.</p> : null}
    </form>
  );
}
