import type { SupabaseClient } from "@supabase/supabase-js";

export type VersionCreateInput = {
  documentId: string;
  organizationId: string;
  title: string;
  contentMarkdown: string;
  contentJson?: unknown;
  createdBy: string;
  changeSummary?: string;
};

/**
 * Creates an immutable document version snapshot before or after a material edit.
 * Keep this server-side so clients cannot forge organization_id or version_number.
 */
export async function createDocumentVersion(
  supabase: SupabaseClient,
  input: VersionCreateInput
) {
  const { data: nextVersion, error: versionError } = await supabase
    .rpc("next_document_version_number", { target_document_id: input.documentId });

  if (versionError) throw versionError;

  const { data, error } = await supabase
    .from("document_versions")
    .insert({
      organization_id: input.organizationId,
      document_id: input.documentId,
      version_number: nextVersion ?? 1,
      title: input.title,
      content_markdown: input.contentMarkdown,
      content_json: input.contentJson ?? null,
      change_summary: input.changeSummary ?? "Manual save",
      created_by: input.createdBy
    })
    .select("id, version_number")
    .single();

  if (error) throw error;
  return data;
}

export function summarizeMarkdownChange(previous: string, next: string) {
  const previousWords = previous.trim().split(/\s+/).filter(Boolean).length;
  const nextWords = next.trim().split(/\s+/).filter(Boolean).length;
  const delta = nextWords - previousWords;

  if (Math.abs(delta) < 10) return "Small content edit";
  if (delta > 0) return `Expanded document by about ${delta} words`;
  return `Shortened document by about ${Math.abs(delta)} words`;
}
