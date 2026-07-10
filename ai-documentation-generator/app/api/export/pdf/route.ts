import { NextRequest, NextResponse } from "next/server";
import { requireUser } from "@/lib/auth/session";
import { recordExport } from "@/lib/export/export-records";
import { renderDocumentHtml } from "@/lib/export/render-document-html";
import { slugify } from "@/lib/slug";

export const runtime = "nodejs";

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

  const fileName = `${slugify(data.title)}.pdf`;

  try {
    // Dynamic import keeps the normal app build light. Install browser binaries
    // locally with: npx playwright install chromium
    const { chromium } = await import("playwright");
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.setContent(renderDocumentHtml({ title: data.title, markdown: data.content_markdown }), {
      waitUntil: "networkidle"
    });
    const pdf = await page.pdf({ format: "A4", printBackground: true, margin: { top: "20mm", right: "18mm", bottom: "20mm", left: "18mm" } });
    await browser.close();

    await recordExport(supabase, {
      organizationId: data.organization_id,
      documentId: data.id,
      userId: user.id,
      format: "pdf",
      status: "created",
      fileName
    });

    return new NextResponse(new Uint8Array(pdf), {
      headers: {
        "content-type": "application/pdf",
        "content-disposition": `attachment; filename="${fileName}"`
      }
    });
  } catch (pdfError) {
    const message = pdfError instanceof Error ? pdfError.message : "PDF export failed";
    await recordExport(supabase, {
      organizationId: data.organization_id,
      documentId: data.id,
      userId: user.id,
      format: "pdf",
      status: "failed",
      fileName,
      errorMessage: message
    });

    return NextResponse.json({
      error: "PDF export is not available in this environment.",
      detail: "Run `npx playwright install chromium` locally or deploy PDF generation to a worker/container with Chromium installed.",
      message
    }, { status: 503 });
  }
}
