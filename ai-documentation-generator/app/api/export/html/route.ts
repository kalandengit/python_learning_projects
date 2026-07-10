import { NextRequest, NextResponse } from "next/server";
import { requireUser } from "@/lib/auth/session";
import { recordExport } from "@/lib/export/export-records";
import { renderDocumentHtml } from "@/lib/export/render-document-html";
import { slugify } from "@/lib/slug";

export async function GET(request: NextRequest) {
  const documentId = request.nextUrl.searchParams.get("document_id");
  if (!documentId) return NextResponse.json({ error: "Missing document_id" }, { status: 400 });

  const { supabase, user } = await requireUser();
  const { data, error } = await supabase
    .from("documents")
    .select("id, organization_id, title, content_markdown")
    .eq("id", documentId)
    .single();

  if (error || !data) return NextResponse.json({ error: "Document not found" }, { status: 404 });

  const fileName = `${slugify(data.title)}.html`;
  const html = renderDocumentHtml({ title: data.title, markdown: data.content_markdown });
  await recordExport(supabase, {
    organizationId: data.organization_id,
    documentId: data.id,
    userId: user.id,
    format: "html",
    status: "created",
    fileName
  });

  return new NextResponse(html, {
    headers: {
      "content-type": "text/html; charset=utf-8",
      "content-disposition": `attachment; filename="${fileName}"`
    }
  });
}
