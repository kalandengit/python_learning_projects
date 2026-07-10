import Link from "next/link";
import { Card } from "@/components/ui/card";
import { requireUser } from "@/lib/auth/session";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";
import type { Upload } from "@/lib/types";

export default async function UploadsPage() {
  const { supabase } = await requireUser();
  const org = await getOrCreateDefaultOrganization();
  const { data, error } = await supabase.from("uploads").select("*").eq("organization_id", org.id).order("created_at", { ascending: false });
  if (error) throw error;
  const uploads = (data ?? []) as Upload[];

  return <div className="space-y-4">
    <h1 className="text-3xl font-bold">Uploads</h1>
    {uploads.length === 0 ? <Card>No uploads yet.</Card> : uploads.map((upload) => (
      <Link href={`/uploads/${upload.id}`} key={upload.id}>
        <Card className="mb-3 hover:bg-slate-50">
          <div className="flex items-center justify-between">
            <div><h2 className="font-semibold">{upload.file_name}</h2><p className="text-sm text-slate-500">{upload.mime_type} · {Math.round(upload.size_bytes / 1024)} KB</p></div>
            <span className="rounded-full border px-3 py-1 text-xs">{upload.status}</span>
          </div>
        </Card>
      </Link>
    ))}
  </div>;
}
