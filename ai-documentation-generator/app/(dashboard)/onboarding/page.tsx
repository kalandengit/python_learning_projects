import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const steps = [
  { title: "Create your first project", description: "Group screenshots and generated docs by product area or customer workflow.", href: "/projects" },
  { title: "Upload 3-5 screenshots", description: "Use a real onboarding or support flow for the best first test.", href: "/upload" },
  { title: "Generate documentation", description: "The AI pipeline turns screenshots into a structured first draft.", href: "/uploads" },
  { title: "Edit and export", description: "Polish the guide, restore versions if needed, then export PDF, HTML, or Markdown.", href: "/documents" },
  { title: "Share with a teammate", description: "Invite collaborators and collect feedback before publishing.", href: "/team" }
];

export default function OnboardingPage() {
  return (
    <div className="space-y-8">
      <div>
        <p className="font-medium text-slate-500">Launch checklist</p>
        <h1 className="text-3xl font-bold tracking-tight">Get to your first useful document in 10 minutes</h1>
        <p className="mt-2 max-w-2xl text-slate-600">This guided flow is designed for beta users and sales demos. Complete each step before inviting a wider team.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {steps.map((step, index) => (
          <Card key={step.title}>
            <CardHeader>
              <CardTitle>{index + 1}. {step.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-4 text-sm text-slate-600">{step.description}</p>
              <Link href={step.href}><Button variant="secondary">Open</Button></Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
