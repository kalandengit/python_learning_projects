import { UploadForm } from "@/components/forms/upload-form";
import { requireUser } from "@/lib/auth/session";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";
import type { Project } from "@/lib/types";

export default async function UploadPage() {
  const { supabase } = await requireUser();
  const org = await getOrCreateDefaultOrganization();
  const { data: projects, error } = await supabase
    .from("projects")
    .select("*")
    .eq("organization_id", org.id)
    .order("created_at", { ascending: false });
  if (error) throw error;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Upload screenshot</h1>
        <p className="mt-2 text-slate-600">Store the screenshot in Supabase Storage and create an upload record for generation.</p>
      </div>
      <UploadForm projects={(projects ?? []) as Project[]} />
    </div>
  );
}
