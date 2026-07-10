import { createAdminClient } from "../lib/supabase/admin";
import { runAiDocumentationJob } from "../lib/ai/job-runner";

const limit = Number(process.env.AI_DRAIN_LIMIT ?? 5);
const supabase = createAdminClient();

async function main() {
  const { data: jobs, error } = await supabase
    .from("ai_jobs")
    .select("id")
    .eq("status", "queued")
    .order("created_at", { ascending: true })
    .limit(limit);

  if (error) throw error;
  if (!jobs?.length) {
    console.log("No queued AI jobs found.");
    return;
  }

  for (const job of jobs) {
    try {
      console.log(`Processing queued AI job ${job.id}...`);
      await runAiDocumentationJob(supabase, job.id);
      console.log(`Completed AI job ${job.id}.`);
    } catch (error) {
      console.error(`Failed AI job ${job.id}:`, error);
      await supabase.from("ai_jobs").update({
        status: "failed",
        error_message: error instanceof Error ? error.message : "Unknown worker error",
        completed_at: new Date().toISOString()
      }).eq("id", job.id);
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
