import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { captureEvent } from "@/lib/analytics/events";
import { writeAuditLog } from "@/lib/audit/log";
import { createNotification } from "@/lib/notifications/notifications";

function appUrl(path: string) {
  return new URL(path, process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000");
}

/**
 * Accepts an invitation link for the currently signed-in user.
 * The signed-in email must exactly match the invited email to prevent link sharing abuse.
 */
export async function GET(_request: Request, context: { params: Promise<{ token: string }> }) {
  const { token } = await context.params;
  const supabase = await createClient();
  const { data: auth } = await supabase.auth.getUser();
  if (!auth.user) {
    return NextResponse.redirect(appUrl(`/login?next=/api/invitations/${token}`));
  }

  const { data: invitation, error } = await supabase
    .from("organization_invitations")
    .select("*")
    .eq("token", token)
    .eq("status", "pending")
    .is("accepted_at", null)
    .single();
  if (error || !invitation) {
    return NextResponse.redirect(appUrl("/team?invite=invalid"));
  }

  const email = auth.user.email?.toLowerCase();
  if (!email || email !== invitation.email) {
    return NextResponse.redirect(appUrl("/team?invite=email_mismatch"));
  }

  if (new Date(invitation.expires_at).getTime() < Date.now()) {
    await supabase.from("organization_invitations").update({ status: "expired" }).eq("id", invitation.id);
    return NextResponse.redirect(appUrl("/team?invite=expired"));
  }

  const { error: memberError } = await supabase.from("organization_members").insert({
    organization_id: invitation.organization_id,
    user_id: auth.user.id,
    role: invitation.role,
    invited_by: invitation.invited_by,
    joined_at: new Date().toISOString()
  });
  if (memberError && memberError.code !== "23505") throw memberError;

  const { error: acceptError } = await supabase
    .from("organization_invitations")
    .update({ status: "accepted", accepted_by: auth.user.id, accepted_at: new Date().toISOString() })
    .eq("id", invitation.id);
  if (acceptError) throw acceptError;

  await captureEvent({
    organizationId: invitation.organization_id,
    userId: auth.user.id,
    eventName: "team_invitation_accepted",
    properties: { invitation_id: invitation.id, role: invitation.role }
  });
  await writeAuditLog({
    organizationId: invitation.organization_id,
    actorUserId: auth.user.id,
    action: "team.invitation.accepted",
    entityType: "organization_invitation",
    entityId: invitation.id,
    metadata: { role: invitation.role }
  });
  await createNotification({
    organizationId: invitation.organization_id,
    userId: invitation.invited_by,
    type: "invitation_accepted",
    title: "Invitation accepted",
    message: `${auth.user.email} joined your workspace.`,
    href: "/team"
  });

  return NextResponse.redirect(appUrl("/team?invite=accepted"));
}
