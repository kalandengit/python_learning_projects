import { z } from "zod";

export const documentAutosaveSchema = z.object({
  content_markdown: z.string().max(200_000, "Document is too large for the MVP editor."),
  title: z.string().min(2).max(120).optional()
});

export const restoreVersionSchema = z.object({
  version_id: z.string().uuid()
});
