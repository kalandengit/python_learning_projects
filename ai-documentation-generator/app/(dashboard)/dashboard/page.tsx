import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { requireUser } from "@/lib/auth/session";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";

export default async function DashboardPage() {
  const { supabase } = await requireUser();
  const org = await getOrCreateDefaultOrganization();
  const [{ count: projectCount }, { count: uploadCount }, { count: documentCount }] = await Promise.all([
    supabase.from("projects").select("id", { count: "exact", head: true }).eq("organization_id", org.id),
    supabase.from("uploads").select("id", { count: "exact", head: true }).eq("organization_id", org.id),
    supabase.from("documents").select("id", { count: "exact", head: true }).eq("organization_id", org.id)
  ]);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-500">Workspace</p>
          <h1 className="text-3xl font-bold">{org.name}</h1>
        </div>
        <Link href="/upload"><Button>Upload screenshot</Button></Link>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Card><p className="text-sm text-slate-500">Projects</p><p className="mt-2 text-3xl font-bold">{projectCount ?? 0}</p></Card>
        <Card><p className="text-sm text-slate-500">Uploads</p><p className="mt-2 text-3xl font-bold">{uploadCount ?? 0}</p></Card>
        <Card><p className="text-sm text-slate-500">Documents</p><p className="mt-2 text-3xl font-bold">{documentCount ?? 0}</p></Card>
      </div>
      <Card>
        <h2 className="mb-2 font-semibold">Sprint 02 workflow</h2>
        <ol className="list-inside list-decimal space-y-1 text-sm text-slate-600">
          <li>Create a project.</li>
          <li>Upload a screenshot.</li>
          <li>Generate AI documentation from the upload detail page.</li>
          <li>Edit, save, export, or share the Markdown document.</li>
        </ol>
      </Card>
    </div>
  );
}
