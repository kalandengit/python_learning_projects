import { AuditLogTable } from "@/components/admin/audit-log-table";
import { createClient } from "@/lib/supabase/server";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";
import type { AuditLog } from "@/lib/types";

export default async function AuditLogsPage() {
  const supabase = await createClient();
  const organization = await getOrCreateDefaultOrganization();
  const { data, error } = await supabase
    .from("audit_logs")
    .select("*")
    .eq("organization_id", organization.id)
    .order("created_at", { ascending: false })
    .limit(100);
  if (error) throw error;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Audit Logs</h1>
        <p className="text-slate-600">Security and compliance history for {organization.name}.</p>
      </div>
      <AuditLogTable logs={(data ?? []) as AuditLog[]} />
    </div>
  );
}
