import { Queue, type JobsOptions } from "bullmq";
import IORedis from "ioredis";

export const AI_DOCUMENTATION_QUEUE = "ai-documentation-generation";

export type AiDocumentationJobPayload = {
  jobId: string;
  uploadId: string;
  userId: string;
  organizationId: string;
};

let queue: Queue<AiDocumentationJobPayload> | null = null;
let connection: IORedis | null = null;

function getRedisConnection() {
  if (!process.env.REDIS_URL) return null;
  if (!connection) {
    connection = new IORedis(process.env.REDIS_URL, {
      maxRetriesPerRequest: null,
      enableReadyCheck: false
    });
  }
  return connection;
}

export function getAiDocumentationQueue() {
  const redis = getRedisConnection();
  if (!redis) return null;
  if (!queue) {
    queue = new Queue<AiDocumentationJobPayload>(AI_DOCUMENTATION_QUEUE, {
      connection: redis,
      defaultJobOptions: defaultAiJobOptions()
    });
  }
  return queue;
}

export function defaultAiJobOptions(): JobsOptions {
  return {
    attempts: Number(process.env.AI_JOB_MAX_ATTEMPTS ?? 3),
    backoff: {
      type: "exponential",
      delay: 15_000
    },
    removeOnComplete: {
      age: 60 * 60 * 24 * 7,
      count: 1000
    },
    removeOnFail: {
      age: 60 * 60 * 24 * 14,
      count: 3000
    }
  };
}

export async function enqueueAiDocumentationJob(payload: AiDocumentationJobPayload) {
  const q = getAiDocumentationQueue();
  if (!q) return { queued: false as const, reason: "REDIS_URL is not configured" };

  const bullJob = await q.add("generate-documentation", payload, {
    jobId: payload.jobId,
    ...defaultAiJobOptions()
  });

  return { queued: true as const, bullJobId: bullJob.id };
}
