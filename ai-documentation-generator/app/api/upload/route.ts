import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

export async function POST(request: Request) {
  const formData = await request.formData();
  const file = formData.get("file");
  if (!(file instanceof File)) redirect("/upload?error=missing_file");

  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const path = `${user.id}/${Date.now()}-${file.name}`;
  const { error } = await supabase.storage.from("uploads").upload(path, file, { upsert: false });
  if (error) redirect("/upload?error=upload_failed");

  redirect(`/documents?uploaded=${encodeURIComponent(path)}`);
}
