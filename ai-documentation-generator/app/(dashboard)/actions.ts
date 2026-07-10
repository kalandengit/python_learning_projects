"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { nanoid } from "nanoid";
import { z } from "zod";
import { requireUser } from "@/lib/auth/session";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";
import { createAiJob } from "@/lib/ai/jobs";
import { enqueueAiDocumentationJob } from "@/lib/jobs/ai-documentation-queue";
import { createDocumentVersion, summarizeMarkdownChange } from "@/lib/documents/versioning";
import { assertQuotaAvailable, recordUsageEvent } from "@/lib/billing/usage";
import { captureEvent } from "@/lib/analytics/events";
import { writeAuditLog } from "@/lib/audit/log";
import { createNotification } from "@/lib/notifications/notifications";
import { sendInvitationEmail } from "@/lib/email/send";

const projectSchema = z.object({
  name: z.string().min(2, "Project name is too short").max(80),
  description: z.string().max(500).optional()
});

export async function createProjectAction(formData: FormData) {
  const { supabase, user } = await requireUser();
  const org = await getOrCreateDefaultOrganization();
  const parsed = projectSchema.safeParse({
    name: formData.get("name"),
    description: formData.get("description") || undefined
  });
  if (!parsed.success) throw new Error(parsed.error.issues[0]?.message || "Invalid project");

  const { error } = await supabase.from("projects").insert({
    organization_id: org.id,
    name: parsed.data.name,
    description: parsed.data.description ?? null,
    created_by: user.id
  });
  if (error) throw error;
  await captureEvent({ organizationId: org.id, userId: user.id, eventName: "project_created", properties: { name: parsed.data.name } });
  revalidatePath("/projects");
  revalidatePath("/dashboard");
}

export async function uploadScreenshotAction(formData: FormData) {
  const { supabase, user } = await requireUser();
  const org = await getOrCreateDefaultOrganization();
  const file = formData.get("file");
  const projectId = String(formData.get("project_id") || "") || null;
  if (!(file instanceof File) || file.size === 0) throw new Error("Please choose a screenshot file.");
  if (!file.type.startsWith("image/")) throw new Error("MVP accepts image screenshots only.");
  if (file.size > 8 * 1024 * 1024) throw new Error("File must be smaller than 8MB for the MVP.");
  await assertQuotaAvailable(supabase, org.id, "upload");

  const extension = file.name.split(".").pop() || "png";
  const storagePath = `${org.id}/${user.id}/${Date.now()}-${nanoid(8)}.${extension}`;

  const { error: storageError } = await supabase.storage.from("uploads").upload(storagePath, file, {
    contentType: file.type,
    upsert: false
  });
  if (storageError) throw storageError;

  const { data: upload, error: uploadError } = await supabase
    .from("uploads")
    .insert({
      organization_id: org.id,
      project_id: projectId,
      user_id: user.id,
      storage_path: storagePath,
      file_name: file.name,
      mime_type: file.type,
      size_bytes: file.size,
      status: "uploaded"
    })
    .select("id")
    .single();
  if (uploadError) throw uploadError;

  await recordUsageEvent(supabase, {
    organizationId: org.id,
    userId: user.id,
    eventType: "upload_created",
    metadata: { upload_id: upload.id, size_bytes: file.size, mime_type: file.type }
  });
  await captureEvent({
    organizationId: org.id,
    userId: user.id,
    eventName: "upload_created",
    properties: { upload_id: upload.id, size_bytes: file.size, mime_type: file.type }
  });

  revalidatePath("/uploads");
  redirect(`/uploads/${upload.id}`);
}

export async function generateDocumentFromUploadAction(formData: FormData) {
  const { supabase, user } = await requireUser();
  const uploadId = String(formData.get("upload_id") || "");
  if (!uploadId) throw new Error("Missing upload id.");

  const { data: upload, error: uploadError } = await supabase
    .from("uploads")
    .select("*")
    .eq("id", uploadId)
    .single();
  if (uploadError || !upload) throw uploadError || new Error("Upload not found");

  await assertQuotaAvailable(supabase, upload.organization_id, "document_generation");

  await supabase.from("uploads").update({ status: "processing", error_message: null }).eq("id", uploadId);

  const jobId = await createAiJob(supabase, {
    organizationId: upload.organization_id,
    userId: user.id,
    uploadId: upload.id
  });

  const enqueueResult = await enqueueAiDocumentationJob({
    jobId,
    uploadId: upload.id,
    userId: user.id,
    organizationId: upload.organization_id
  });

  await supabase.from("ai_jobs").update({
    queue_provider: enqueueResult.queued ? "bullmq" : "database",
    queue_job_id: enqueueResult.queued ? enqueueResult.bullJobId : null
  }).eq("id", jobId);

  await captureEvent({
    organizationId: upload.organization_id,
    userId: user.id,
    eventName: "ai_generation_requested",
    properties: { upload_id: upload.id, job_id: jobId, queued: enqueueResult.queued }
  });

  revalidatePath(`/uploads/${uploadId}`);
  redirect(`/uploads/${uploadId}?job=${jobId}`);
}

export async function updateDocumentMarkdownAction(formData: FormData) {
  const { supabase, user } = await requireUser();
  const id = String(formData.get("document_id") || "");
  const markdown = String(formData.get("content_markdown") || "");
  const title = String(formData.get("title") || "").trim();
  if (!id) throw new Error("Missing document id");

  const { data: current, error: readError } = await supabase
    .from("documents")
    .select("id, organization_id, title, content_markdown, content_json")
    .eq("id", id)
    .single();
  if (readError || !current) throw readError || new Error("Document not found");

  const nextTitle = title || current.title;
  const changeSummary = summarizeMarkdownChange(current.content_markdown || "", markdown);

  const { error } = await supabase
    .from("documents")
    .update({
      title: nextTitle,
      content_markdown: markdown,
      last_edited_by: user.id
    })
    .eq("id", id);
  if (error) throw error;

  await captureEvent({ organizationId: current.organization_id, userId: user.id, eventName: "document_saved", properties: { document_id: id } });

  await createDocumentVersion(supabase, {
    documentId: id,
    organizationId: current.organization_id,
    title: nextTitle,
    contentMarkdown: markdown,
    contentJson: current.content_json,
    createdBy: user.id,
    changeSummary
  });

  revalidatePath(`/documents/${id}`);
}

export async function createShareLinkAction(formData: FormData) {
  const { supabase, user } = await requireUser();
  const id = String(formData.get("document_id") || "");
  const shareToken = nanoid(24);
  const { data: document, error: readError } = await supabase.from("documents").select("organization_id").eq("id", id).single();
  if (readError || !document) throw readError || new Error("Document not found");
  const { error } = await supabase.from("documents").update({ visibility: "shared", share_token: shareToken }).eq("id", id);
  if (error) throw error;
  await captureEvent({ organizationId: document.organization_id, userId: user.id, eventName: "share_link_created", properties: { document_id: id } });
  revalidatePath(`/documents/${id}`);
}


export async function restoreDocumentVersionAction(formData: FormData) {
  const { supabase, user } = await requireUser();
  const documentId = String(formData.get("document_id") || "");
  const versionId = String(formData.get("version_id") || "");
  if (!documentId || !versionId) throw new Error("Missing document or version id");

  const { data: version, error: versionError } = await supabase
    .from("document_versions")
    .select("*")
    .eq("id", versionId)
    .eq("document_id", documentId)
    .single();
  if (versionError || !version) throw versionError || new Error("Version not found");

  const { error } = await supabase
    .from("documents")
    .update({
      title: version.title,
      content_markdown: version.content_markdown,
      content_json: version.content_json,
      last_edited_by: user.id
    })
    .eq("id", documentId);
  if (error) throw error;

  await captureEvent({ organizationId: version.organization_id, userId: user.id, eventName: "document_version_restored", properties: { document_id: documentId, version_id: versionId } });

  await createDocumentVersion(supabase, {
    documentId,
    organizationId: version.organization_id,
    title: version.title,
    contentMarkdown: version.content_markdown,
    contentJson: version.content_json,
    createdBy: user.id,
    changeSummary: `Restored version ${version.version_number}`
  });

  revalidatePath(`/documents/${documentId}`);
}

const invitationSchema = z.object({
  organizationId: z.string().uuid(),
  email: z.string().email().transform((value) => value.toLowerCase().trim()),
  role: z.enum(["admin", "member"])
});

const memberRoleSchema = z.object({
  organizationId: z.string().uuid(),
  userId: z.string().uuid(),
  role: z.enum(["admin", "member"])
});

/** Invite a teammate. Admin+ only; invitation acceptance still verifies the signed-in user's email. */
export async function inviteMemberAction(formData: FormData) {
  const { supabase, user } = await requireUser();
  const parsed = invitationSchema.safeParse({
    organizationId: formData.get("organization_id"),
    email: formData.get("email"),
    role: formData.get("role")
  });
  if (!parsed.success) throw new Error(parsed.error.issues[0]?.message || "Invalid invitation");

  const { requireOrgRole } = await import("@/lib/collaboration/permissions");
  await requireOrgRole(parsed.data.organizationId, "admin");

  const expiresAt = new Date(Date.now() + 1000 * 60 * 60 * 24 * 7).toISOString();
  const token = nanoid(40);
  const { data: organization, error: orgError } = await supabase
    .from("organizations")
    .select("name")
    .eq("id", parsed.data.organizationId)
    .single();
  if (orgError || !organization) throw orgError || new Error("Organization not found");

  const { data: invitation, error } = await supabase.from("organization_invitations").insert({
    organization_id: parsed.data.organizationId,
    email: parsed.data.email,
    role: parsed.data.role,
    token,
    invited_by: user.id,
    expires_at: expiresAt
  }).select("id, token").single();
  if (error) throw error;

  const acceptUrl = `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}/api/invitations/${token}`;
  await sendInvitationEmail({
    to: parsed.data.email,
    organizationName: organization.name,
    inviterEmail: user.email,
    acceptUrl
  });
  await writeAuditLog({
    organizationId: parsed.data.organizationId,
    actorUserId: user.id,
    action: "team.invitation.created",
    entityType: "organization_invitation",
    entityId: invitation.id,
    metadata: { email: parsed.data.email, role: parsed.data.role }
  });

  await captureEvent({
    organizationId: parsed.data.organizationId,
    userId: user.id,
    eventName: "team_invitation_created",
    properties: { role: parsed.data.role }
  });
  revalidatePath("/team");
}

export async function revokeInvitationAction(formData: FormData) {
  const { supabase, user } = await requireUser();
  const organizationId = String(formData.get("organization_id") || "");
  const invitationId = String(formData.get("invitation_id") || "");
  if (!organizationId || !invitationId) throw new Error("Missing invitation details");
  const { requireOrgRole } = await import("@/lib/collaboration/permissions");
  await requireOrgRole(organizationId, "admin");

  const { error } = await supabase
    .from("organization_invitations")
    .update({ status: "revoked" })
    .eq("id", invitationId)
    .eq("organization_id", organizationId);
  if (error) throw error;

  await captureEvent({ organizationId, userId: user.id, eventName: "team_invitation_revoked", properties: { invitation_id: invitationId } });
  await writeAuditLog({ organizationId, actorUserId: user.id, action: "team.invitation.revoked", entityType: "organization_invitation", entityId: invitationId });
  revalidatePath("/team");
}

export async function updateMemberRoleAction(formData: FormData) {
  const { supabase, user } = await requireUser();
  const parsed = memberRoleSchema.safeParse({
    organizationId: formData.get("organization_id"),
    userId: formData.get("user_id"),
    role: formData.get("role")
  });
  if (!parsed.success) throw new Error(parsed.error.issues[0]?.message || "Invalid role update");
  if (parsed.data.userId === user.id) throw new Error("You cannot change your own role.");

  const { requireOrgRole } = await import("@/lib/collaboration/permissions");
  await requireOrgRole(parsed.data.organizationId, "owner");

  const { error } = await supabase
    .from("organization_members")
    .update({ role: parsed.data.role })
    .eq("organization_id", parsed.data.organizationId)
    .eq("user_id", parsed.data.userId)
    .neq("role", "owner");
  if (error) throw error;

  await captureEvent({ organizationId: parsed.data.organizationId, userId: user.id, eventName: "team_member_role_updated", properties: { target_user_id: parsed.data.userId, role: parsed.data.role } });
  await writeAuditLog({ organizationId: parsed.data.organizationId, actorUserId: user.id, action: "team.member.role_updated", entityType: "organization_member", metadata: { target_user_id: parsed.data.userId, role: parsed.data.role } });
  await createNotification({ organizationId: parsed.data.organizationId, userId: parsed.data.userId, type: "role_updated", title: "Your role changed", message: `Your workspace role is now ${parsed.data.role}.`, href: "/team" });
  revalidatePath("/team");
}

export async function removeMemberAction(formData: FormData) {
  const { supabase, user } = await requireUser();
  const organizationId = String(formData.get("organization_id") || "");
  const userId = String(formData.get("user_id") || "");
  if (!organizationId || !userId) throw new Error("Missing member details");
  if (userId === user.id) throw new Error("You cannot remove yourself from the workspace.");

  const { requireOrgRole } = await import("@/lib/collaboration/permissions");
  await requireOrgRole(organizationId, "owner");

  const { error } = await supabase
    .from("organization_members")
    .delete()
    .eq("organization_id", organizationId)
    .eq("user_id", userId)
    .neq("role", "owner");
  if (error) throw error;

  await captureEvent({ organizationId, userId: user.id, eventName: "team_member_removed", properties: { target_user_id: userId } });
  await writeAuditLog({ organizationId, actorUserId: user.id, action: "team.member.removed", entityType: "organization_member", metadata: { target_user_id: userId } });
  revalidatePath("/team");
}


const profileSchema = z.object({
  fullName: z.string().max(120).optional(),
  jobTitle: z.string().max(120).optional(),
  timezone: z.string().max(80).optional()
});

export async function updateProfileAction(formData: FormData) {
  const { supabase, user } = await requireUser();
  const parsed = profileSchema.safeParse({
    fullName: formData.get("full_name") || undefined,
    jobTitle: formData.get("job_title") || undefined,
    timezone: formData.get("timezone") || undefined
  });
  if (!parsed.success) throw new Error(parsed.error.issues[0]?.message || "Invalid profile");

  const { error } = await supabase.from("profiles").upsert({
    user_id: user.id,
    full_name: parsed.data.fullName ?? null,
    job_title: parsed.data.jobTitle ?? null,
    timezone: parsed.data.timezone ?? "UTC"
  });
  if (error) throw error;
  revalidatePath("/settings");
}

export async function markNotificationReadAction(formData: FormData) {
  const { supabase } = await requireUser();
  const id = String(formData.get("notification_id") || "");
  if (!id) throw new Error("Missing notification id");
  const { error } = await supabase.from("notifications").update({ read_at: new Date().toISOString() }).eq("id", id);
  if (error) throw error;
  revalidatePath("/notifications");
}

export async function markAllNotificationsReadAction() {
  const { supabase, user } = await requireUser();
  const { error } = await supabase
    .from("notifications")
    .update({ read_at: new Date().toISOString() })
    .eq("user_id", user.id)
    .is("read_at", null);
  if (error) throw error;
  revalidatePath("/notifications");
}
