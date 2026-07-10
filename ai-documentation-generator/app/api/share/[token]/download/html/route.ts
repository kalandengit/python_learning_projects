import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { renderDocumentHtml } from "@/lib/export/render-document-html";
import { slugify } from "@/lib/slug";

export async function GET(_request: NextRequest, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("documents")
    .select("title, content_markdown")
    .eq("share_token", token)
    .in("visibility", ["shared", "public"])
    .single();

  if (error || !data) return NextResponse.json({ error: "Shared document not found" }, { status: 404 });

  const html = renderDocumentHtml({ title: data.title, markdown: data.content_markdown });
  return new NextResponse(html, {
    headers: {
      "content-type": "text/html; charset=utf-8",
      "content-disposition": `attachment; filename="${slugify(data.title)}.html"`
    }
  });
}
