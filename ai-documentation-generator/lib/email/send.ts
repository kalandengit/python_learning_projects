import { Resend } from "resend";

const resend = process.env.RESEND_API_KEY ? new Resend(process.env.RESEND_API_KEY) : null;

export async function sendInvitationEmail(input: {
  to: string;
  organizationName: string;
  inviterEmail?: string | null;
  acceptUrl: string;
}) {
  if (!resend) {
    console.warn("RESEND_API_KEY is not configured. Invitation link:", input.acceptUrl);
    return { skipped: true };
  }

  const from = process.env.EMAIL_FROM || "DocuPilot AI <onboarding@resend.dev>";
  const subject = `You're invited to ${input.organizationName} on DocuPilot AI`;
  const html = `
    <div style="font-family:Inter,Arial,sans-serif;line-height:1.6;color:#0f172a">
      <h1 style="font-size:22px">Join ${input.organizationName}</h1>
      <p>${input.inviterEmail || "A teammate"} invited you to collaborate on AI-generated documentation.</p>
      <p><a href="${input.acceptUrl}" style="display:inline-block;background:#0f172a;color:white;padding:12px 18px;border-radius:10px;text-decoration:none">Accept invitation</a></p>
      <p style="color:#64748b;font-size:13px">This invitation expires in 7 days. If you did not expect this email, you can ignore it.</p>
    </div>`;

  return resend.emails.send({ from, to: input.to, subject, html });
}
