import Link from "next/link";
import { notFound } from "next/navigation";
import { createShareLinkAction } from "@/app/(dashboard)/actions";
import { DocumentMetadata } from "@/components/documents/document-metadata";
import { ExportActions } from "@/components/documents/export-actions";
import { MarkdownEditorForm } from "@/components/documents/markdown-editor-form";
import { VersionHistory, type DocumentVersionListItem } from "@/components/documents/version-history";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { requireUser } from "@/lib/auth/session";
import type { Document } from "@/lib/types";

type ExtendedDocument = Document & {
  word_count?: number | null;
  last_saved_at?: string | null;
};

export default async function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { supabase } = await requireUser();
  const { data, error } = await supabase.from("documents").select("*").eq("id", id).single();
  if (error || !data) notFound();
  const document = data as ExtendedDocument;

  const { data: versions } = await supabase
    .from("document_versions")
    .select("id, version_number, title, change_summary, created_at, created_by")
    .eq("document_id", document.id)
    .order("version_number", { ascending: false })
    .limit(20);

  const shareUrl = document.share_token ? `/share/${document.share_token}` : null;

  return <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
    <div className="space-y-4">
      <div>
        <p className="text-sm font-medium text-slate-500">Document editor</p>
        <h1 className="text-3xl font-bold">{document.title}</h1>
      </div>
      <MarkdownEditorForm documentId={document.id} initialTitle={document.title} initialMarkdown={document.content_markdown} />
    </div>
    <div className="space-y-4">
      <Card className="h-fit space-y-4">
        <h2 className="font-semibold">Actions</h2>
        <ExportActions documentId={document.id} />
        {shareUrl ? <Link href={shareUrl} target="_blank"><Button type="button" variant="secondary" className="w-full">Open share link</Button></Link> : (
          <form action={createShareLinkAction}>
            <input type="hidden" name="document_id" value={document.id} />
            <Button type="submit" variant="secondary" className="w-full">Create share link</Button>
          </form>
        )}
        <p className="text-xs text-slate-500">Sprint 06 adds Markdown, HTML, and PDF export plus a polished share surface.</p>
      </Card>
      <Card className="space-y-4">
        <h2 className="font-semibold">Metadata</h2>
        <DocumentMetadata wordCount={document.word_count} lastSavedAt={document.last_saved_at} />
      </Card>
      <Card className="space-y-4">
        <h2 className="font-semibold">Version history</h2>
        <VersionHistory documentId={document.id} versions={(versions ?? []) as DocumentVersionListItem[]} />
      </Card>
    </div>
  </div>;
}
