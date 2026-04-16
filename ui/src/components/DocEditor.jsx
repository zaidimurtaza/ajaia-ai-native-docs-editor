import Placeholder from "@tiptap/extension-placeholder";
import Underline from "@tiptap/extension-underline";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useEffect, useRef, useState } from "react";
import {
  getContentByLink,
  getDocumentContent,
  putContentByLink,
  putDocumentContent,
} from "../api.js";
import { EditorSkeleton } from "./LoadingSkeleton.jsx";
import { EditorToolbar } from "./EditorToolbar.jsx";

const emptyDoc = { type: "doc", content: [] };

export function DocEditor({ docId, authToken, shareQsToken, linkSlug, detail }) {
  const canEdit = detail.role === "owner" || detail.role === "editor";
  const [ready, setReady] = useState(false);
  const [err, setErr] = useState(null);
  const saveTimer = useRef();

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
      }),
      Underline,
      Placeholder.configure({ placeholder: canEdit ? "Start writing…" : "Read only" }),
    ],
    editable: canEdit,
    editorProps: {
      attributes: {
        class: "tiptap",
      },
    },
  });

  useEffect(() => {
    editor?.setEditable(canEdit);
  }, [editor, canEdit]);

  useEffect(() => {
    if (!editor) return;
    let cancelled = false;
    (async () => {
      try {
        const pack = linkSlug
          ? await getContentByLink(linkSlug)
          : await getDocumentContent(authToken, docId, shareQsToken);
        if (cancelled) return;
        const c = pack.content;
        if (c && typeof c === "object") {
          editor.commands.setContent(c);
        } else if (!detail.has_content && detail.initial_content) {
          const esc = detail.initial_content
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
          editor.commands.setContent(`<p>${esc.replace(/\n/g, "</p><p>")}</p>`);
        } else {
          editor.commands.setContent(emptyDoc);
        }
        setReady(true);
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Load failed");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [docId, authToken, shareQsToken, linkSlug, editor, detail.has_content, detail.initial_content]);

  useEffect(() => {
    if (!editor || !canEdit || !ready) return;
    const save = () => {
      window.clearTimeout(saveTimer.current);
      saveTimer.current = window.setTimeout(() => {
        const json = editor.getJSON();
        const p = linkSlug
          ? putContentByLink(linkSlug, json)
          : putDocumentContent(authToken, docId, json, shareQsToken);
        void p.catch(() => {});
      }, 1200);
    };
    editor.on("update", save);
    return () => {
      editor.off("update", save);
      window.clearTimeout(saveTimer.current);
    };
  }, [editor, canEdit, ready, docId, authToken, shareQsToken, linkSlug]);

  if (err) return <div className="error-banner">{err}</div>;
  if (!editor || !ready) return <EditorSkeleton />;

  return (
    <div className="editor-with-toolbar">
      {canEdit ? <EditorToolbar editor={editor} /> : <div className="editor-toolbar ro-bar">View only</div>}
      <EditorContent editor={editor} className="editor-frame" />
    </div>
  );
}
