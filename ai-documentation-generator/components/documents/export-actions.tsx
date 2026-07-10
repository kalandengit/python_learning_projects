import { Button } from "@/components/ui/button";

export function ExportActions({ documentId }: { documentId: string }) {
  return (
    <div className="space-y-2">
      <a href={`/api/export/markdown?document_id=${documentId}`}>
        <Button type="button" variant="secondary" className="w-full">Download Markdown</Button>
      </a>
      <a href={`/api/export/html?document_id=${documentId}`}>
        <Button type="button" variant="secondary" className="w-full">Download HTML</Button>
      </a>
      <a href={`/api/export/pdf?document_id=${documentId}`}>
        <Button type="button" variant="secondary" className="w-full">Download PDF</Button>
      </a>
    </div>
  );
}
