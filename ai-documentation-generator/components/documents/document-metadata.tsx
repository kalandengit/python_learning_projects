export function DocumentMetadata({ wordCount, lastSavedAt }: { wordCount?: number | null; lastSavedAt?: string | null }) {
  return <div className="grid grid-cols-2 gap-3 text-sm">
    <div className="rounded-xl border border-slate-200 p-3">
      <p className="text-xs text-slate-500">Words</p>
      <p className="font-semibold">{wordCount ?? 0}</p>
    </div>
    <div className="rounded-xl border border-slate-200 p-3">
      <p className="text-xs text-slate-500">Last saved</p>
      <p className="font-semibold">{lastSavedAt ? new Date(lastSavedAt).toLocaleTimeString() : "Not saved"}</p>
    </div>
  </div>;
}
