"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

type JobState = {
  id: string;
  status: "queued" | "processing" | "completed" | "failed" | "cancelled";
  document_id: string | null;
  error_message: string | null;
  attempts?: number;
  max_attempts?: number;
};

export function JobStatusPoller({ initialJob, uploadId }: { initialJob: JobState; uploadId: string }) {
  const [job, setJob] = useState<JobState>(initialJob);
  const [isPending, startTransition] = useTransition();

  const isTerminal = useMemo(() => ["completed", "failed", "cancelled"].includes(job.status), [job.status]);

  useEffect(() => {
    if (isTerminal) return;

    const interval = window.setInterval(async () => {
      const response = await fetch(`/api/jobs/${job.id}`, { cache: "no-store" });
      if (!response.ok) return;
      const payload = await response.json();
      setJob(payload.job);
    }, 2500);

    return () => window.clearInterval(interval);
  }, [job.id, isTerminal]);

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">Current generation job</p>
          <p className="mt-1 text-sm text-slate-600">
            Status: <span className="font-medium text-slate-900">{job.status}</span>
            {typeof job.attempts === "number" && typeof job.max_attempts === "number" ? ` · Attempts ${job.attempts}/${job.max_attempts}` : ""}
          </p>
          {job.error_message ? <p className="mt-2 text-sm text-red-700">{job.error_message}</p> : null}
        </div>
        {!isTerminal ? <span className="h-3 w-3 animate-pulse rounded-full bg-slate-900" aria-label="Processing" /> : null}
      </div>

      {job.status === "completed" && job.document_id ? (
        <Link
          href={`/documents/${job.document_id}`}
          className="mt-4 inline-flex items-center justify-center rounded-xl bg-slate-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
        >
          Open generated document
        </Link>
      ) : null}

      {job.status === "failed" ? (
        <form action="/uploads/[id]" className="mt-4">
          <Button type="button" onClick={() => startTransition(() => window.location.assign(`/uploads/${uploadId}`))} disabled={isPending}>
            Return to upload and retry
          </Button>
        </form>
      ) : null}
    </div>
  );
}
