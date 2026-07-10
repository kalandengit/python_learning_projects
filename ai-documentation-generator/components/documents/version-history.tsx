import { restoreDocumentVersionAction } from "@/app/(dashboard)/actions";
import { Button } from "@/components/ui/button";

export type DocumentVersionListItem = {
  id: string;
  version_number: number;
  title: string;
  change_summary: string | null;
  created_at: string;
  created_by: string | null;
};

export function VersionHistory({ documentId, versions }: { documentId: string; versions: DocumentVersionListItem[] }) {
  if (versions.length === 0) {
    return <p className="text-sm text-slate-500">No saved versions yet. Save the document to create the first snapshot.</p>;
  }

  return <div className="space-y-3">
    {versions.map((version) => (
      <div key={version.id} className="rounded-xl border border-slate-200 p-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">Version {version.version_number}</p>
            <p className="text-xs text-slate-500">{new Date(version.created_at).toLocaleString()}</p>
            <p className="mt-1 text-xs text-slate-600">{version.change_summary ?? "Saved snapshot"}</p>
          </div>
          <form action={restoreDocumentVersionAction}>
            <input type="hidden" name="document_id" value={documentId} />
            <input type="hidden" name="version_id" value={version.id} />
            <Button type="submit" variant="secondary">Restore</Button>
          </form>
        </div>
      </div>
    ))}
  </div>;
}
