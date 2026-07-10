import { PostHog } from "posthog-node";
import { createAdminClient } from "@/lib/supabase/admin";

type AnalyticsProperties = Record<string, string | number | boolean | null | undefined>;

let posthogClient: PostHog | null = null;

function getPostHog() {
  if (!process.env.POSTHOG_API_KEY) return null;
  if (!posthogClient) {
    posthogClient = new PostHog(process.env.POSTHOG_API_KEY, {
      host: process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com",
      flushAt: 1,
      flushInterval: 0
    });
  }
  return posthogClient;
}

/**
 * Server-side analytics capture.
 * Writes durable first-party events to Supabase and mirrors to PostHog when configured.
 */
export async function captureEvent(input: {
  organizationId: string;
  userId?: string | null;
  eventName: string;
  source?: "server" | "client" | "worker" | "webhook";
  properties?: AnalyticsProperties;
}) {
  const properties = Object.fromEntries(
    Object.entries(input.properties || {}).filter(([, value]) => value !== undefined)
  );

  const supabase = createAdminClient();
  const { error } = await supabase.from("analytics_events").insert({
    organization_id: input.organizationId,
    user_id: input.userId ?? null,
    event_name: input.eventName,
    source: input.source ?? "server",
    properties
  });

  if (error) {
    console.error("Failed to write analytics event", { event: input.eventName, error });
  }

  const posthog = getPostHog();
  if (posthog) {
    posthog.capture({
      distinctId: input.userId || input.organizationId,
      event: input.eventName,
      properties: {
        organization_id: input.organizationId,
        source: input.source ?? "server",
        ...properties
      }
    });
  }
}
