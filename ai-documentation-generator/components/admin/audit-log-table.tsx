import type { AuditLog } from "@/lib/types";

export function AuditLogTable({ logs }: { logs: AuditLog[] }) {
  return (
    <div className="overflow-hidden rounded-2xl border bg-white">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-slate-600">
          <tr>
            <th className="p-4">Time</th>
            <th className="p-4">Action</th>
            <th className="p-4">Entity</th>
            <th className="p-4">Actor</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id} className="border-t">
              <td className="p-4 text-slate-600">{new Date(log.created_at).toLocaleString()}</td>
              <td className="p-4 font-medium">{log.action}</td>
              <td className="p-4">{log.entity_type}</td>
              <td className="p-4 text-slate-600">{log.actor_user_id ?? "system"}</td>
            </tr>
          ))}
          {logs.length === 0 ? <tr><td className="p-6 text-slate-600" colSpan={4}>No audit logs yet.</td></tr> : null}
        </tbody>
      </table>
    </div>
  );
}
