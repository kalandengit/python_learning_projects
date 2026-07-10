import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

/** Server-side auth guard used by dashboard pages and server actions. */
export async function requireUser() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getUser();
  if (error || !data.user) redirect("/login");
  return { supabase, user: data.user };
}
