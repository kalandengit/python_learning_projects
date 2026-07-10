import { NextRequest, NextResponse } from "next/server";
import { requireUser } from "@/lib/auth/session";
import { recordExport } from "@/lib/export/export-records";
import { slugify } from "@/lib/slug";

export async function GET(request: NextRequest) {
  const documentId = request.nextUrl.searchParams.get("document_id");
  if (!documentId) return NextResponse.json({ error: "Missing document_id" }, { status: 400 });
  const { supabase, user } = await requireUser();
  const { data, error } = await supabase.from("documents").select("id, organization_id, title, content_markdown").eq("id", documentId).single();
  if (error || !data) return NextResponse.json({ error: "Document not found" }, { status: 404 });
  const fileName = `${slugify(data.title)}.md`;
  await recordExport(supabase, {
    organizationId: data.organization_id,
    documentId: data.id,
    userId: user.id,
    format: "markdown",
    status: "created",
    fileName
  });

  return new NextResponse(data.content_markdown, {
    headers: {
      "content-type": "text/markdown; charset=utf-8",
      "content-disposition": `attachment; filename="${fileName}"`
    }
  });
}
