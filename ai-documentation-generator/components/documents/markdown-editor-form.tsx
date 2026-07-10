"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { updateDocumentMarkdownAction } from "@/app/(dashboard)/actions";
import { Input } from "@/components/ui/input";

export function MarkdownEditorForm({
  documentId,
  initialTitle,
  initialMarkdown
}: {
  documentId: string;
  initialTitle: string;
  initialMarkdown: string;
}) {
  const [title, setTitle] = useState(initialTitle);
  const [value, setValue] = useState(initialMarkdown);
  const wordCount = useMemo(() => value.trim().split(/\s+/).filter(Boolean).length, [value]);

  return (
    <form action={updateDocumentMarkdownAction} className="space-y-4">
      <input type="hidden" name="document_id" value={documentId} />
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="document-title">Document title</label>
        <Input id="document-title" name="title" value={title} onChange={(event) => setTitle(event.target.value)} />
      </div>
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>Markdown editor</span>
        <span>{wordCount} words</span>
      </div>
      <textarea
        name="content_markdown"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        className="min-h-[540px] w-full rounded-2xl border bg-white p-5 font-mono text-sm shadow-sm outline-none focus:ring-2 focus:ring-slate-300"
      />
      <div className="flex items-center gap-3">
        <Button type="submit">Save changes</Button>
        <p className="text-xs text-slate-500">Every manual save creates a restorable version snapshot.</p>
      </div>
    </form>
  );
}
