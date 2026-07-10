import { NextResponse } from "next/server";
import { requireUser } from "@/lib/auth/session";
import { createDocumentVersion, summarizeMarkdownChange } from "@/lib/documents/versioning";
import { documentAutosaveSchema } from "@/lib/validators/document-version";

/**
 * Autosaves editor content and records a version snapshot.
 * In production, debounce client calls to 5-10 seconds and add rate limiting.
 */
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { supabase, user } = await requireUser();
  const body = await request.json().catch(() => null);
  const parsed = documentAutosaveSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0]?.message || "Invalid payload" }, { status: 400 });
  }

  const { data: current, error: readError } = await supabase
    .from("documents")
    .select("id, organization_id, title, content_markdown, content_json")
    .eq("id", id)
    .single();

  if (readError || !current) {
    return NextResponse.json({ error: "Document not found" }, { status: 404 });
  }

  const nextTitle = parsed.data.title || current.title;
  const nextMarkdown = parsed.data.content_markdown;

  const { error: updateError } = await supabase
    .from("documents")
    .update({ title: nextTitle, content_markdown: nextMarkdown, last_edited_by: user.id })
    .eq("id", id);

  if (updateError) {
    return NextResponse.json({ error: updateError.message }, { status: 500 });
  }

  const version = await createDocumentVersion(supabase, {
    documentId: id,
    organizationId: current.organization_id,
    title: nextTitle,
    contentMarkdown: nextMarkdown,
    contentJson: current.content_json,
    createdBy: user.id,
    changeSummary: summarizeMarkdownChange(current.content_markdown || "", nextMarkdown)
  });

  return NextResponse.json({ ok: true, saved_at: new Date().toISOString(), version });
}
