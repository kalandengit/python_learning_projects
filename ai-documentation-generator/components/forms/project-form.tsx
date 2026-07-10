import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createProjectAction } from "@/app/(dashboard)/actions";

export function ProjectForm() {
  return (
    <form action={createProjectAction} className="space-y-3 rounded-2xl border bg-white p-5 shadow-sm">
      <h2 className="font-semibold">Create project</h2>
      <Input name="name" placeholder="Example: Customer onboarding guides" required />
      <Input name="description" placeholder="Optional description" />
      <Button type="submit">Create project</Button>
    </form>
  );
}
