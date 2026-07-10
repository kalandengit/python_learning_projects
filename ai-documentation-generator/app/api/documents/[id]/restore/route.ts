import { NextResponse } from "next/server";
import { requireUser } from "@/lib/auth/session";
import { createDocumentVersion } from "@/lib/documents/versioning";
import { restoreVersionSchema } from "@/lib/validators/document-version";

export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { supabase, user } = await requireUser();
  const body = await request.json().catch(() => null);
  const parsed = restoreVersionSchema.safeParse(body);
  if (!parsed.success) return NextResponse.json({ error: "Invalid version id" }, { status: 400 });

  const { data: version, error: versionError } = await supabase
    .from("document_versions")
    .select("*")
    .eq("id", parsed.data.version_id)
    .eq("document_id", id)
    .single();
  if (versionError || !version) return NextResponse.json({ error: "Version not found" }, { status: 404 });

  const { error: updateError } = await supabase
    .from("documents")
    .update({
      title: version.title,
      content_markdown: version.content_markdown,
      content_json: version.content_json,
      last_edited_by: user.id
    })
    .eq("id", id);
  if (updateError) return NextResponse.json({ error: updateError.message }, { status: 500 });

  const restoreSnapshot = await createDocumentVersion(supabase, {
    documentId: id,
    organizationId: version.organization_id,
    title: version.title,
    contentMarkdown: version.content_markdown,
    contentJson: version.content_json,
    createdBy: user.id,
    changeSummary: `Restored version ${version.version_number}`
  });

  return NextResponse.json({ ok: true, version: restoreSnapshot });
}
