import { requireUser } from "@/lib/auth/session";

export async function getCurrentProfile() {
  const { supabase, user } = await requireUser();
  const { data, error } = await supabase.from("profiles").select("*").eq("user_id", user.id).maybeSingle();
  if (error) throw error;
  if (data) return data;
  const { data: created, error: createError } = await supabase
    .from("profiles")
    .insert({ user_id: user.id, full_name: user.user_metadata?.full_name || user.email?.split("@")[0] || null })
    .select("*")
    .single();
  if (createError) throw createError;
  return created;
}
