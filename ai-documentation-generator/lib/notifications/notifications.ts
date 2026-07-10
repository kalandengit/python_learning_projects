import { createClient } from "@/lib/supabase/server";

export type NotificationInput = {
  organizationId: string;
  userId: string;
  type: string;
  title: string;
  message: string;
  href?: string | null;
  metadata?: Record<string, unknown>;
};

export async function createNotification(input: NotificationInput) {
  const supabase = await createClient();
  const { error } = await supabase.from("notifications").insert({
    organization_id: input.organizationId,
    user_id: input.userId,
    type: input.type,
    title: input.title,
    message: input.message,
    href: input.href ?? null,
    metadata: input.metadata ?? {}
  });
  if (error) console.error("notification_create_failed", error);
}

export async function listNotifications(limit = 30) {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("notifications")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(limit);
  if (error) throw error;
  return data ?? [];
}
