"use client";

import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";

export function DocumentEditor({ initialContent }: { initialContent?: string }) {
  const editor = useEditor({
    extensions: [StarterKit, Placeholder.configure({ placeholder: "Start writing or generate documentation from a screenshot..." })],
    content: initialContent ?? "",
    editorProps: {
      attributes: { class: "prose-editor prose max-w-none" }
    },
    immediatelyRender: false
  });

  return <EditorContent editor={editor} />;
}
