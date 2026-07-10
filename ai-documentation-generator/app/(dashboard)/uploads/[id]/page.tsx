import { notFound } from "next/navigation";
import { generateDocumentFromUploadAction } from "@/app/(dashboard)/actions";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { requireUser } from "@/lib/auth/session";
import type { AiJob, Upload } from "@/lib/types";
import { AiJobHistory } from "@/components/uploads/ai-job-history";
import { JobStatusPoller } from "@/components/jobs/job-status-poller";

export default async function UploadDetailPage({
  params,
  searchParams
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ job?: string }>;
}) {
  const { id } = await params;
  const { job: activeJobId } = await searchParams;
  const { supabase } = await requireUser();

  const { data, error } = await supabase.from("uploads").select("*").eq("id", id).single();
  if (error || !data) notFound();
  const upload = data as Upload;

  const { data: signed } = await supabase.storage.from("uploads").createSignedUrl(upload.storage_path, 60 * 5);
  const { data: jobsData } = await supabase.from("ai_jobs").select("*").eq("upload_id", upload.id).order("created_at", { ascending: false });
  const jobs = (jobsData || []) as AiJob[];
  const activeJob = jobs.find((job) => job.id === activeJobId) ?? jobs.find((job) => ["queued", "processing"].includes(job.status));

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
      <Card>
        {signed?.signedUrl ? (
          <img src={signed.signedUrl} alt={upload.file_name} className="w-full rounded-xl border" />
        ) : (
          <p>Preview unavailable.</p>
        )}
      </Card>

      <div className="space-y-4">
        <Card className="h-fit space-y-4">
          <div>
            <h1 className="text-xl font-bold">{upload.file_name}</h1>
            <p className="text-sm text-slate-500">Status: {upload.status}</p>
          </div>
          {upload.error_message ? <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{upload.error_message}</p> : null}
          <form action={generateDocumentFromUploadAction}>
            <input type="hidden" name="upload_id" value={upload.id} />
            <Button type="submit" disabled={upload.status === "processing"}>Queue documentation generation</Button>
          </form>
          <p className="text-xs text-slate-500">
            Sprint 04 queues generation work instead of blocking the request. Run the worker with <code>npm run worker:ai</code>, or use <code>npm run jobs:drain</code> for DB-only local processing.
          </p>
        </Card>

        {activeJob ? <JobStatusPoller initialJob={activeJob as any} uploadId={upload.id} /> : null}
        <AiJobHistory jobs={jobs} />
      </div>
    </div>
  );
}
