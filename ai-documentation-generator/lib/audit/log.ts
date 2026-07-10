import { createClient } from "@/lib/supabase/server";

type AuditInput = {
  organizationId: string;
  actorUserId: string | null;
  action: string;
  entityType: string;
  entityId?: string | null;
  metadata?: Record<string, unknown>;
};

/** Writes a compliance-friendly audit log. Keep metadata non-sensitive. */
export async function writeAuditLog(input: AuditInput) {
  const supabase = await createClient();
  const { error } = await supabase.rpc("insert_audit_log", {
    p_organization_id: input.organizationId,
    p_actor_user_id: input.actorUserId,
    p_action: input.action,
    p_entity_type: input.entityType,
    p_entity_id: input.entityId ?? null,
    p_metadata: input.metadata ?? {}
  });
  if (error) {
    // Do not block the user path on audit failure in the MVP, but surface it in server logs.
    console.error("audit_log_failed", error);
  }
}
