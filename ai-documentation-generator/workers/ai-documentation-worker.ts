import { Worker } from "bullmq";
import IORedis from "ioredis";
import { createAdminClient } from "../lib/supabase/admin";
import { AI_DOCUMENTATION_QUEUE, type AiDocumentationJobPayload } from "../lib/jobs/ai-documentation-queue";
import { runAiDocumentationJob } from "../lib/ai/job-runner";

const redisUrl = process.env.REDIS_URL;
if (!redisUrl) {
  throw new Error("REDIS_URL is required for the BullMQ worker. Use npm run jobs:drain for DB-only local processing.");
}

const connection = new IORedis(redisUrl, {
  maxRetriesPerRequest: null,
  enableReadyCheck: false
});

const supabase = createAdminClient();
const concurrency = Number(process.env.AI_WORKER_CONCURRENCY ?? 2);

const worker = new Worker<AiDocumentationJobPayload>(
  AI_DOCUMENTATION_QUEUE,
  async (job) => {
    await supabase.from("ai_jobs").update({ queue_job_id: job.id, queue_provider: "bullmq" }).eq("id", job.data.jobId);
    return runAiDocumentationJob(supabase, job.data.jobId);
  },
  { connection, concurrency }
);

worker.on("completed", (job) => {
  console.log(`[ai-worker] completed job ${job.id}`);
});

worker.on("failed", async (job, error) => {
  console.error(`[ai-worker] failed job ${job?.id}:`, error);
  if (job?.data?.jobId) {
    await supabase.from("ai_jobs").update({
      status: "failed",
      error_message: error.message,
      completed_at: new Date().toISOString()
    }).eq("id", job.data.jobId);
  }
});

async function shutdown(signal: string) {
  console.log(`[ai-worker] received ${signal}; closing worker...`);
  await worker.close();
  await connection.quit();
  process.exit(0);
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));

console.log(`[ai-worker] listening on ${AI_DOCUMENTATION_QUEUE} with concurrency=${concurrency}`);
