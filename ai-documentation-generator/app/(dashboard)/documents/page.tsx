import Link from "next/link";
import { Card } from "@/components/ui/card";
import { requireUser } from "@/lib/auth/session";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";
import type { Document } from "@/lib/types";

export default async function DocumentsPage() {
  const { supabase } = await requireUser();
  const org = await getOrCreateDefaultOrganization();
  const { data, error } = await supabase.from("documents").select("*").eq("organization_id", org.id).order("updated_at", { ascending: false });
  if (error) throw error;
  const documents = (data ?? []) as Document[];

  return <div className="space-y-4">
    <h1 className="text-3xl font-bold">Documents</h1>
    {documents.length === 0 ? <Card>No generated documents yet. Upload a screenshot to create one.</Card> : documents.map((document) => (
      <Link href={`/documents/${document.id}`} key={document.id}>
        <Card className="mb-3 hover:bg-slate-50">
          <h2 className="font-semibold">{document.title}</h2>
          <p className="mt-1 line-clamp-2 text-sm text-slate-600">{document.content_markdown.slice(0, 180)}</p>
        </Card>
      </Link>
    ))}
  </div>;
}
