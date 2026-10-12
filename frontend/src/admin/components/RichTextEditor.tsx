import { useEffect, useRef, useState } from "react";
import { useEditor, useEditorState, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Image from "@tiptap/extension-image";
import TextAlign from "@tiptap/extension-text-align";
import { uploadMedia } from "@/api/admin";
import MediaLibraryModal from "./MediaLibraryModal";
import { PreservedBlock } from "./PreservedBlock";

interface RichTextEditorProps {
  label: string;
  value: string;
  onChange: (html: string) => void;
  /** Offers the "Fayl qo'shish" button. Only the Uzbek editor takes it: the server reads new files from the Uzbek text. */
  allowFiles?: boolean;
  /**
   * The page keeps its text as legacy HTML (see apps/content/raw_editing.py): links, alignment and a PDF added
   * as a link all survive, so the toolbar offers them. Block-by-block pages keep plain text only, where a link
   * mark would be dropped on save.
   */
  rawHtml?: boolean;
}

const DOCUMENT_ACCEPT = ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx";
const FILE_LINK_RE = /\.(pdf|docx?|xlsx?|pptx?)(?:[?#]|$)/i;

function escapeHtml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/** "Hujjat (PDF/fayl) Nizom — tahrirlanmaydi" -> "Nizom": the caption of a PDF card chip. */
function captionFromChipLabel(label: string): string {
  const match = /^Hujjat(?: \(PDF\/fayl\))?\s*(.*?)\s*(?:—.*)?$/.exec(label);
  return match?.[1]?.trim() || "";
}

/** "Nizom_2026_ab12CdE.pdf" -> "Nizom 2026" -- the title the file's card gets unless the editor renames it. */
function titleFromFileName(name: string): string {
  return name.replace(/\.[A-Za-z0-9]{2,5}$/, "").replace(/[_\s]+/g, " ").trim() || "Hujjat";
}

interface ToolbarButtonProps {
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
  title: string;
  icon: string;
}

function ToolbarButton({ active, disabled, onClick, title, icon }: ToolbarButtonProps) {
  return (
    <button
      type="button"
      title={title}
      disabled={disabled}
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
      className={`w-8 h-8 flex items-center justify-center rounded-md text-base cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
        active ? "bg-primary-500 text-background-50" : "text-foreground-600 hover:bg-background-200"
      }`}
    >
      <i className={icon} />
    </button>
  );
}

/**
 * TipTap-based WYSIWYG editor for content_* fields. Legacy data is
 * CKEditor-authored HTML — TipTap's StarterKit round-trips the common tags
 * that content actually uses (p/strong/em/ul/ol/a/img/h2-h3/blockquote)
 * cleanly; more exotic CKEditor-only inline styling may not survive a
 * resave pixel-for-pixel, but the content stays intact and editable.
 * Blocks the editor can't express (tables, PDFs, galleries, staff cards)
 * appear as dashed chips (PreservedBlock) and are kept as-is on save.
 * A "Kod" (HTML source) toggle is kept for anyone who wants to hand-edit
 * markup the visual toolbar doesn't expose.
 */
export default function RichTextEditor({ label, value, onChange, allowFiles = false, rawHtml = false }: RichTextEditorProps) {
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const documentInputRef = useRef<HTMLInputElement>(null);
  const replaceInputRef = useRef<HTMLInputElement>(null);
  const [uploadError, setUploadError] = useState("");
  const [linkOpen, setLinkOpen] = useState(false);
  const [linkUrl, setLinkUrl] = useState("");
  const lastEmittedHtml = useRef(value);

  const editor = useEditor({
    extensions: [
      // StarterKit v3 already bundles Underline and Link -- registering them again as separate
      // extensions logged "Duplicate extension names" on every editor mount.
      // No target/rel on links the editor writes: a page link must keep opening in the same tab, as it does today.
      StarterKit.configure({ link: { openOnClick: false, autolink: true, HTMLAttributes: { target: null, rel: null } } }),
      // width/height stay on the picture when its page is edited: they reserve its space while it loads.
      Image.extend({
        addAttributes() {
          return { ...this.parent?.(), width: { default: null }, height: { default: null } };
        },
      }),
      TextAlign.configure({ types: ["heading", "paragraph"] }),
      PreservedBlock,
    ],
    content: value,
    onUpdate: ({ editor }) => {
      const html = editor.getHTML();
      lastEmittedHtml.current = html;
      onChange(html);
    },
    editorProps: {
      attributes: {
        // .preserved-block: a table/PDF/gallery the editor can't edit as text (see PreservedBlock.ts).
        class:
          "prose max-w-none min-h-[220px] px-4 py-3 focus:outline-none [&_img]:max-w-full [&_img]:max-h-72 [&_img]:w-auto [&_img]:rounded-md " +
          "[&_.preserved-block]:my-3 [&_.preserved-block]:cursor-grab [&_.preserved-block]:select-none [&_.preserved-block]:rounded-md " +
          "[&_.preserved-block]:border [&_.preserved-block]:border-dashed [&_.preserved-block]:border-primary-400 " +
          "[&_.preserved-block]:bg-primary-50 [&_.preserved-block]:px-3 [&_.preserved-block]:py-2.5 " +
          "[&_.preserved-block]:text-sm [&_.preserved-block]:font-medium [&_.preserved-block]:text-primary-700 " +
          "[&_.preserved-block.ProseMirror-selectednode]:border-solid [&_.preserved-block.ProseMirror-selectednode]:ring-2 [&_.preserved-block.ProseMirror-selectednode]:ring-primary-500",
      },
    },
  });

  // What is under the cursor, for the "replace file" button: a link to a document, or a selected PDF card.
  const cursor = useEditorState({
    editor,
    selector: ({ editor: current }) => {
      if (!current) return { linkHref: null as string | null, cardLabel: null as string | null };
      const href = (current.getAttributes("link").href as string | undefined) ?? null;
      const selected = (current.state.selection as { node?: { type: { name: string }; attrs: Record<string, unknown> } }).node;
      const isCard = selected?.type.name === "preservedBlock" && selected.attrs.blockType === "document";
      return { linkHref: href, cardLabel: isCard ? String(selected?.attrs.label ?? "") : null };
    },
  });
  const canReplaceLinkedFile = Boolean(rawHtml && cursor?.linkHref && FILE_LINK_RE.test(cursor.linkHref));
  const canReplaceCard = Boolean(allowFiles && cursor?.cardLabel !== null && cursor?.cardLabel !== undefined);

  // Syncs external value changes (e.g. async data load on an edit page,
  // where this component mounts before the fetch resolves) into the editor.
  // Guarded against the editor's own onUpdate so it doesn't fight typing.
  useEffect(() => {
    if (!editor) return;
    if (value !== lastEmittedHtml.current && value !== editor.getHTML()) {
      editor.commands.setContent(value, { emitUpdate: false });
      lastEmittedHtml.current = value;
    }
  }, [value, editor]);

  function insertImage(url: string) {
    editor?.chain().focus().setImage({ src: url }).run();
  }

  async function onUploadFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadMedia(file);
      insertImage(result.url);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function onUploadDocument(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !editor) return;
    setUploading(true);
    setUploadError("");
    try {
      const result = await uploadMedia(file);
      const title = titleFromFileName(file.name);
      if (!allowFiles) {
        // ru/en tab of a legacy page: the file goes into this language's own text as a link; the public page
        // turns a link that stands alone on a line into the same document card.
        editor.chain().focus().insertContent(`<p><a href="${escapeHtml(result.url)}">${escapeHtml(title)}</a></p>`).run();
        return;
      }
      editor
        .chain()
        .focus()
        .insertContent({
          type: "preservedBlock",
          attrs: {
            newDocument: result.path,
            docTitle: title,
            blockType: "document",
            label: `Hujjat: ${title} (saqlaganingizda sahifaga qo'shiladi)`,
          },
        })
        .run();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Faylni yuklab bo'lmadi.");
    } finally {
      setUploading(false);
      if (documentInputRef.current) documentInputRef.current.value = "";
    }
  }

  async function onReplaceFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !editor) return;
    setUploading(true);
    setUploadError("");
    try {
      const result = await uploadMedia(file);
      if (canReplaceCard) {
        // The old card is removed and a new one (same caption) takes its place when the page is saved.
        const title = captionFromChipLabel(cursor?.cardLabel ?? "") || titleFromFileName(file.name);
        editor
          .chain()
          .focus()
          .insertContent({
            type: "preservedBlock",
            attrs: {
              newDocument: result.path,
              docTitle: title,
              blockType: "document",
              label: `Hujjat: ${title} (saqlaganingizda sahifaga qo'shiladi)`,
            },
          })
          .run();
      } else if (canReplaceLinkedFile) {
        editor.chain().focus().extendMarkRange("link").setLink({ href: result.url }).run();
      }
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Faylni yuklab bo'lmadi.");
    } finally {
      setUploading(false);
      if (replaceInputRef.current) replaceInputRef.current.value = "";
    }
  }

  function openLinkEditor() {
    setLinkUrl((editor?.getAttributes("link").href as string | undefined) ?? "");
    setLinkOpen(true);
  }

  function applyLink() {
    if (!editor) return;
    let url = linkUrl.trim();
    if (!url) {
      editor.chain().focus().extendMarkRange("link").unsetLink().run();
    } else {
      if (/^www\./i.test(url)) url = "https://" + url;
      if (editor.state.selection.empty && !editor.isActive("link")) {
        editor.chain().focus().insertContent(`<a href="${escapeHtml(url)}">${escapeHtml(url)}</a>`).run();
      } else {
        editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
      }
    }
    setLinkOpen(false);
  }

  return (
    <div>
      <div className="mb-1.5">
        <label className="block text-sm font-medium text-foreground-700">{label}</label>
      </div>

      {(
        <div className="rounded-md border border-background-300 bg-background-50 overflow-hidden">
          {editor && (
            <div className="flex flex-wrap items-center gap-0.5 px-2 py-1.5 border-b border-background-200 bg-background-100">
              <ToolbarButton title="Qalin" icon="ri-bold" active={editor.isActive("bold")} onClick={() => editor.chain().focus().toggleBold().run()} />
              <ToolbarButton title="Kursiv" icon="ri-italic" active={editor.isActive("italic")} onClick={() => editor.chain().focus().toggleItalic().run()} />
              <ToolbarButton title="Tagiga chizilgan" icon="ri-underline" active={editor.isActive("underline")} onClick={() => editor.chain().focus().toggleUnderline().run()} />
              <ToolbarButton title="Chizilgan" icon="ri-strikethrough" active={editor.isActive("strike")} onClick={() => editor.chain().focus().toggleStrike().run()} />
              <span className="w-px h-5 bg-background-300 mx-1" />
              <ToolbarButton title="Sarlavha 2" icon="ri-h-2" active={editor.isActive("heading", { level: 2 })} onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} />
              <ToolbarButton title="Sarlavha 3" icon="ri-h-3" active={editor.isActive("heading", { level: 3 })} onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()} />
              <span className="w-px h-5 bg-background-300 mx-1" />
              <ToolbarButton title="Ro'yxat (belgili)" icon="ri-list-unordered" active={editor.isActive("bulletList")} onClick={() => editor.chain().focus().toggleBulletList().run()} />
              <ToolbarButton title="Ro'yxat (raqamli)" icon="ri-list-ordered" active={editor.isActive("orderedList")} onClick={() => editor.chain().focus().toggleOrderedList().run()} />
              <ToolbarButton title="Iqtibos" icon="ri-double-quotes-l" active={editor.isActive("blockquote")} onClick={() => editor.chain().focus().toggleBlockquote().run()} />
              {rawHtml && (
                <>
                  <span className="w-px h-5 bg-background-300 mx-1" />
                  <ToolbarButton title="Havola qo'shish / tahrirlash" icon="ri-link" active={editor.isActive("link")} onClick={openLinkEditor} />
                  <ToolbarButton title="Chapga" icon="ri-align-left" active={editor.isActive({ textAlign: "left" })} onClick={() => editor.chain().focus().setTextAlign("left").run()} />
                  <ToolbarButton title="O'rtaga" icon="ri-align-center" active={editor.isActive({ textAlign: "center" })} onClick={() => editor.chain().focus().setTextAlign("center").run()} />
                  <ToolbarButton title="O'ngga" icon="ri-align-right" active={editor.isActive({ textAlign: "right" })} onClick={() => editor.chain().focus().setTextAlign("right").run()} />
                </>
              )}
              <span className="w-px h-5 bg-background-300 mx-1" />
              <ToolbarButton title="Rasm (yuklash)" icon={uploading ? "ri-loader-4-line animate-spin" : "ri-image-add-line"} onClick={() => fileInputRef.current?.click()} />
              <ToolbarButton title="Rasm (kutubxonadan)" icon="ri-folder-image-line" onClick={() => setLibraryOpen(true)} />
              {(allowFiles || rawHtml) && (
                <ToolbarButton
                  title={allowFiles ? "Fayl qo'shish (PDF, Word, Excel...)" : "Fayl qo'shish (havola bo'lib qo'shiladi)"}
                  icon={uploading ? "ri-loader-4-line animate-spin" : "ri-file-upload-line"}
                  onClick={() => documentInputRef.current?.click()}
                />
              )}
              {(canReplaceLinkedFile || canReplaceCard) && (
                <button
                  type="button"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => replaceInputRef.current?.click()}
                  className="ml-1 h-8 px-3 rounded-md bg-accent-500 text-background-50 text-xs font-semibold cursor-pointer hover:bg-accent-600 flex items-center gap-1.5"
                >
                  <i className={uploading ? "ri-loader-4-line animate-spin" : "ri-refresh-line"} /> Faylni almashtirish
                </button>
              )}
              <span className="w-px h-5 bg-background-300 mx-1" />
              <ToolbarButton title="Bekor qilish" icon="ri-arrow-go-back-line" disabled={!editor.can().undo()} onClick={() => editor.chain().focus().undo().run()} />
              <ToolbarButton title="Qaytarish" icon="ri-arrow-go-forward-line" disabled={!editor.can().redo()} onClick={() => editor.chain().focus().redo().run()} />
            </div>
          )}
          {linkOpen && (
            <div className="flex flex-wrap items-center gap-2 px-3 py-2 border-b border-background-200 bg-primary-50">
              <input
                autoFocus
                value={linkUrl}
                onChange={(e) => setLinkUrl(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    applyLink();
                  }
                }}
                placeholder="https://... (bo'sh qoldirsangiz havola olib tashlanadi)"
                className="flex-1 min-w-[220px] h-9 px-3 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500"
              />
              <button type="button" onClick={applyLink} className="h-9 px-3 rounded-md bg-primary-500 text-background-50 text-xs font-semibold cursor-pointer">Qo'llash</button>
              <button type="button" onClick={() => setLinkOpen(false)} className="h-9 px-3 rounded-md border border-background-300 text-xs cursor-pointer">Yopish</button>
            </div>
          )}
          <EditorContent editor={editor} />
        </div>
      )}
      <p className="mt-1.5 text-xs text-foreground-500">
        Havolani (https://...) matn ichiga shunchaki yozing, sayt uni avtomatik bosiladigan qiladi.
        {allowFiles && " PDF/Word/Excel faylni yuqoridagi fayl belgisi bilan qo'shing: sahifada tayyor karta bo'lib chiqadi."}
        {rawHtml && !allowFiles && " Fayl belgisi faylni shu tilning matniga havola qilib qo'shadi (sahifada tayyor karta bo'lib chiqadi)."}
        {rawHtml && " Matndagi PDF havolasini almashtirish uchun: havola ustiga bosing, «Faylni almashtirish» tugmasi chiqadi."}
      </p>
      {uploadError && <p role="alert" className="mt-1 text-xs text-accent-600">{uploadError}</p>}

      <input ref={fileInputRef} type="file" className="hidden" accept=".jpg,.jpeg,.png,.gif,.webp" onChange={onUploadFile} />
      <input ref={documentInputRef} type="file" className="hidden" accept={DOCUMENT_ACCEPT} onChange={onUploadDocument} />
      <input ref={replaceInputRef} type="file" className="hidden" accept={DOCUMENT_ACCEPT} onChange={onReplaceFile} />
      {libraryOpen && (
        <MediaLibraryModal
          onSelect={(_path, url) => {
            insertImage(url);
            setLibraryOpen(false);
          }}
          onClose={() => setLibraryOpen(false)}
        />
      )}
    </div>
  );
}
