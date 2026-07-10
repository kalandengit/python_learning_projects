import { uploadScreenshotAction } from "@/app/(dashboard)/actions";
import { Button } from "@/components/ui/button";
import type { Project } from "@/lib/types";

export function UploadForm({ projects }: { projects: Project[] }) {
  return (
    <form action={uploadScreenshotAction} className="space-y-4 rounded-2xl border bg-white p-6 shadow-sm">
      <div>
        <label className="mb-2 block text-sm font-medium">Project</label>
        <select name="project_id" className="w-full rounded-xl border bg-white px-3 py-2 text-sm">
          <option value="">No project</option>
          {projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
        </select>
      </div>
      <div>
        <label className="mb-2 block text-sm font-medium">Screenshot</label>
        <input name="file" type="file" accept="image/*" required className="w-full rounded-xl border bg-white px-3 py-2 text-sm" />
        <p className="mt-2 text-xs text-slate-500">PNG/JPG/WebP under 8MB. Videos and PDFs are V2.</p>
      </div>
      <Button type="submit">Upload screenshot</Button>
    </form>
  );
}
