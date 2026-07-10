import { Card } from "@/components/ui/card";
import type { AiJob } from "@/lib/types";

export function AiJobHistory({ jobs }: { jobs: AiJob[] }) {
  if (!jobs.length) {
    return <Card className="text-sm text-slate-500">No AI generation jobs yet.</Card>;
  }

  return <Card className="space-y-3">
    <h2 className="font-semibold">AI job history</h2>
    <div className="space-y-3">
      {jobs.map((job) => (
        <div key={job.id} className="rounded-xl border p-3 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="font-medium capitalize">{job.status}</span>
            <span className="text-xs text-slate-500">{new Date(job.created_at).toLocaleString()}</span>
          </div>
          <p className="mt-1 text-slate-500">Provider: {job.provider}{job.model ? ` / ${job.model}` : ""}</p>
          {job.total_tokens > 0 && <p className="text-slate-500">Tokens: {job.total_tokens.toLocaleString()} · Est. cost: ${Number(job.estimated_cost_usd).toFixed(6)}</p>}
          {job.error_message && <p className="mt-2 rounded-lg bg-red-50 p-2 text-red-700">{job.error_message}</p>}
        </div>
      ))}
    </div>
  </Card>;
}
