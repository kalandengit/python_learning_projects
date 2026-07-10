import { notFound } from "next/navigation";
import { marked } from "marked";
import { SharedDocumentToolbar } from "@/components/share/shared-document-toolbar";
import { createClient } from "@/lib/supabase/server";
import type { Document } from "@/lib/types";

export default async function SharedDocumentPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const supabase = await createClient();
  const { data, error } = await supabase.from("documents").select("*").eq("share_token", token).in("visibility", ["shared", "public"]).single();
  if (error || !data) notFound();
  const document = data as Document;
  const html = marked.parse(document.content_markdown, { async: false });
  return <main className="mx-auto max-w-4xl px-6 py-10">
    <SharedDocumentToolbar token={token} />
    <article className="prose prose-slate max-w-none rounded-2xl border bg-white p-8 shadow-sm md:p-10" dangerouslySetInnerHTML={{ __html: html }} />
  </main>;
}
