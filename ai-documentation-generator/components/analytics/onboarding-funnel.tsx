const steps = [
  ["workspace_created", "Workspace"],
  ["project_created", "Project"],
  ["upload_created", "Upload"],
  ["ai_generation_requested", "AI generation"],
  ["document_created", "Document"],
  ["export_created", "Export"]
] as const;

export function OnboardingFunnel({ funnel }: { funnel: Record<string, number> | null | undefined }) {
  return (
    <div className="grid gap-3 md:grid-cols-6">
      {steps.map(([key, label], index) => (
        <div key={key} className="rounded-xl border bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Step {index + 1}</p>
          <p className="mt-1 font-semibold">{label}</p>
          <p className="mt-2 text-2xl font-bold">{Number(funnel?.[key] || 0)}</p>
        </div>
      ))}
    </div>
  );
}
