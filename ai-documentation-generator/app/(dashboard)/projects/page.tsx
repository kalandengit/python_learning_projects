import { ProjectForm } from "@/components/forms/project-form";
import { Card } from "@/components/ui/card";
import { requireUser } from "@/lib/auth/session";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";
import type { Project } from "@/lib/types";

export default async function ProjectsPage() {
  const { supabase } = await requireUser();
  const org = await getOrCreateDefaultOrganization();
  const { data: projects, error } = await supabase
    .from("projects")
    .select("*")
    .eq("organization_id", org.id)
    .order("created_at", { ascending: false });
  if (error) throw error;

  return (
    <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
      <ProjectForm />
      <div className="space-y-3">
        <h1 className="text-2xl font-bold">Projects</h1>
        {(projects as Project[]).length === 0 ? <Card>No projects yet.</Card> : (projects as Project[]).map((project) => (
          <Card key={project.id}>
            <h2 className="font-semibold">{project.name}</h2>
            {project.description && <p className="mt-1 text-sm text-slate-600">{project.description}</p>}
          </Card>
        ))}
      </div>
    </div>
  );
}
