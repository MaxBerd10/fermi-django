import { useEffect, useRef, useState } from "react";
import { uploadMedia } from "@/api/admin";
import LangTabs from "../LangTabs";
import MediaLibraryModal from "../MediaLibraryModal";
import type { Lang } from "../LangTabs";
import {
  DOCUMENT_STYLES, GALLERY_STYLES, MAP_HEIGHT, addColumn, addPictures, addRow, embedProblem, galleryProblem, galleryStaged, movePicture, removePicture, setGalleryStyle, setPictureAlt, mapSrcFrom, removeColumn, removeRow, setCell, setDocumentCaption, setDocumentStyle,
  setEmbedField, setGroupLabel, setGroupSpans, setHeader, tableProblem, youtubeIdFrom,
  type DocumentData, type EmbedData, type GalleryForm, type TableData,
} from "@/admin/lib/blockForms";

export type EditableBlockType = "table" | "embed" | "document" | "gallery";

interface Props {
  blockType: EditableBlockType;
  /** "new": a block that is being added; "edit": one the page already has. */
  mode: "new" | "edit";
  initial: unknown;
  /** A document card: which file it is for (the file cannot be changed in this form). */
  documentInfo?: { title: string; filename: string } | null;
  onApply: (data: unknown) => void;
  onClose: () => void;
}

const FIELD = "w-full h-9 px-2.5 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500";
const SMALL_BUTTON = "h-8 px-2.5 rounded-md border border-background-300 bg-background-50 text-xs font-medium text-foreground-700 hover:bg-background-100 cursor-pointer";

const TITLES: Record<EditableBlockType, string> = { table: "Jadval", embed: "Video / xarita", document: "Hujjat kartasi", gallery: "Rasmlar galereyasi" };

export default function BlockEditorModal({ blockType, mode, initial, documentInfo, onApply, onClose }: Props) {
  const [data, setData] = useState<unknown>(initial);
  const [lang, setLang] = useState<Lang>("uz");
  const [problem, setProblem] = useState("");

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function apply() {
    const found = blockType === "table" ? tableProblem(data as TableData)
      : blockType === "embed" ? embedProblem(data as EmbedData)
      : blockType === "gallery" ? galleryProblem(data as GalleryForm)
      : null;
    if (found) {
      setProblem(found);
      return;
    }
    onApply(blockType === "gallery" ? galleryStaged(data as GalleryForm) : data);
  }

  return (
    <div className="fixed inset-0 z-[80] flex items-start justify-center overflow-y-auto bg-black/40 p-4 md:p-10" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div role="dialog" aria-modal="true" aria-label={TITLES[blockType]} className="w-full max-w-4xl rounded-xl bg-background-50 shadow-2xl">
        <div className="flex items-center justify-between gap-3 border-b border-background-200 px-5 py-3.5">
          <h2 className="text-base font-semibold text-foreground-900">{TITLES[blockType]} {mode === "new" ? "qo'shish" : "tahrirlash"}</h2>
          <LangTabs value={lang} onChange={setLang} />
        </div>
        <div className="px-5 py-4">
          {blockType === "table" && <TableForm data={data as TableData} lang={lang} onChange={setData} />}
          {blockType === "embed" && <EmbedForm data={data as EmbedData} lang={lang} onChange={setData} />}
          {blockType === "document" && <DocumentForm data={data as DocumentData} lang={lang} info={documentInfo ?? null} onChange={setData} />}
          {blockType === "gallery" && <GalleryFormView data={data as GalleryForm} lang={lang} onChange={setData} />}
          {problem && <p role="alert" className="mt-3 text-sm text-red-600">{problem}</p>}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-background-200 bg-background-100 px-5 py-3 rounded-b-xl">
          <p className="text-xs text-foreground-500">O'zgarish sahifani «Saqlash» bilan saqlaganingizda kuchga kiradi. Tillarning hammasi shu oynada.</p>
          <div className="flex gap-2">
            <button type="button" onClick={onClose} className="h-9 px-4 rounded-md border border-background-300 text-sm cursor-pointer">Bekor qilish</button>
            <button type="button" onClick={apply} className="h-9 px-4 rounded-md bg-primary-500 text-background-50 text-sm font-semibold cursor-pointer hover:bg-primary-600">Qo'llash</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------------------------- table

function TableForm({ data, lang, onChange }: { data: TableData; lang: Lang; onChange: (next: TableData) => void }) {
  const table = data[lang];
  const groups = table.header_groups;
  const covered = groups?.reduce((sum, group) => sum + group.span, 0) ?? 0;
  return (
    <div className="space-y-4">
      <p className="text-xs text-foreground-500">
        Qator va ustun qo'shish yoki olib tashlash uch tilda birga bo'ladi. Katak matnlarini har til uchun alohida yozing (tepadagi UZ / RU / EN).
      </p>
      <div className="overflow-x-auto rounded-md border border-background-300">
        <table className="w-full border-collapse text-sm">
          <thead>
            {groups && (
              <tr className="bg-primary-50">
                {groups.map((group, index) => (
                  <th key={index} colSpan={group.span} className="border border-background-300 p-1 align-top">
                    <input aria-label={`Guruh ${index + 1} sarlavhasi`} className={FIELD} placeholder="Guruh sarlavhasi (bo'sh bo'lishi mumkin)" value={group.label} onChange={(e) => onChange(setGroupLabel(data, lang, index, e.target.value))} />
                  </th>
                ))}
                <th className="w-8 border-0" />
              </tr>
            )}
            <tr className="bg-background-100">
              {table.headers.map((header, column) => (
                <th key={column} className="min-w-[6.5rem] border border-background-300 p-1 align-top">
                  <input aria-label={`Ustun ${column + 1} sarlavhasi`} className={`${FIELD} font-semibold`} placeholder="Sarlavha" value={header} onChange={(e) => onChange(setHeader(data, lang, column, e.target.value))} />
                  {table.headers.length > 1 && (
                    <button type="button" title="Ustunni olib tashlash" onClick={() => onChange(removeColumn(data, column))} className="mt-1 w-full text-[11px] text-red-600 cursor-pointer hover:underline"><i className="ri-close-line" /> ustun</button>
                  )}
                </th>
              ))}
              <th className="w-8 border-0" />
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, r) => (
              <tr key={r}>
                {row.map((cell, c) => (
                  <td key={c} className="min-w-[6.5rem] border border-background-300 p-1">
                    <input aria-label={`Qator ${r + 1}, ustun ${c + 1}`} className={FIELD} value={cell} onChange={(e) => onChange(setCell(data, lang, r, c, e.target.value))} />
                  </td>
                ))}
                <td className="w-8 text-center">
                  {table.rows.length > 1 && (
                    <button type="button" title="Qatorni olib tashlash" aria-label={`Qator ${r + 1} ni olib tashlash`} onClick={() => onChange(removeRow(data, r))} className="text-red-600 cursor-pointer"><i className="ri-close-line" /></button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap gap-2">
        <button type="button" className={SMALL_BUTTON} onClick={() => onChange(addRow(data))}><i className="ri-add-line" /> Qator</button>
        <button type="button" className={SMALL_BUTTON} onClick={() => onChange(addColumn(data))}><i className="ri-add-line" /> Ustun</button>
      </div>
      <div className="rounded-md border border-background-200 bg-background-100 p-3">
        <label className="flex items-center gap-2 text-sm font-medium text-foreground-800">
          <input
            type="checkbox"
            checked={Boolean(groups)}
            onChange={(e) => onChange(setGroupSpans(data, e.target.checked ? [data.uz.headers.length] : []))}
          />
          Sarlavhalar ustida guruh sarlavhasi qatori
        </label>
        {groups && (
          <div className="mt-2 space-y-1.5">
            <p className="text-xs text-foreground-500">Har guruh nechta ustunni qoplaydi (guruhlar tilga bog'liq emas; yozuvni yuqoridagi jadvalda kiriting).</p>
            <div className="flex flex-wrap items-center gap-2">
              {groups.map((group, index) => (
                <label key={index} className="flex items-center gap-1 text-xs">
                  Guruh {index + 1}:
                  <input
                    type="number"
                    min={1}
                    max={table.headers.length}
                    className="h-8 w-16 rounded-md border border-background-300 px-2 text-sm"
                    value={group.span}
                    onChange={(e) => onChange(setGroupSpans(data, groups.map((g, i) => (i === index ? Math.max(1, Number(e.target.value) || 1) : g.span))))}
                  />
                </label>
              ))}
              <button type="button" className={SMALL_BUTTON} onClick={() => onChange(setGroupSpans(data, [...groups.map((g) => g.span), 1]))}>+ guruh</button>
              {groups.length > 1 && <button type="button" className={SMALL_BUTTON} onClick={() => onChange(setGroupSpans(data, groups.slice(0, -1).map((g) => g.span)))}>− guruh</button>}
            </div>
            <p className={`text-xs ${covered === table.headers.length ? "text-green-700" : "text-red-600"}`}>Qoplangan ustunlar: {covered} / {table.headers.length}</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------------------------- embed

function EmbedForm({ data, lang, onChange }: { data: EmbedData; lang: Lang; onChange: (next: EmbedData) => void }) {
  const first = data.uz;
  const [pasted, setPasted] = useState(first.provider === "youtube" ? first.video_id : first.src);
  const recognized = first.provider === "youtube" ? youtubeIdFrom(pasted) : mapSrcFrom(pasted);
  function paste(value: string) {
    setPasted(value);
    if (first.provider === "youtube") onChange(setEmbedField(data, "video_id", youtubeIdFrom(value) ?? ""));
    else onChange(setEmbedField(data, "src", mapSrcFrom(value) ?? ""));
  }
  return (
    <div className="space-y-4">
      {first.provider === "youtube" ? (
        <>
          <label className="block text-sm font-medium text-foreground-800">YouTube havolasi
            <input className={`${FIELD} mt-1`} placeholder="https://youtu.be/..." value={pasted} onChange={(e) => paste(e.target.value)} />
          </label>
          <p className={`text-xs ${recognized ? "text-green-700" : "text-foreground-500"}`}>{recognized ? `Video kodi: ${recognized}` : "Havolani (youtu.be/… yoki youtube.com/watch?v=…) yoki 11 belgili video kodini qo'ying."}</p>
          {recognized && (
            <div className="aspect-video max-w-md overflow-hidden rounded-md bg-black">
              <iframe title="Ko'rib chiqish" src={`https://www.youtube-nocookie.com/embed/${recognized}`} className="h-full w-full" loading="lazy" referrerPolicy="no-referrer-when-downgrade" />
            </div>
          )}
        </>
      ) : (
        <>
          <label className="block text-sm font-medium text-foreground-800">Google xarita kodi
            <textarea className={`${FIELD} mt-1 h-24 py-2 font-mono text-xs`} placeholder='<iframe src="https://www.google.com/maps/embed?pb=..." ...></iframe>' value={pasted} onChange={(e) => paste(e.target.value)} />
          </label>
          <p className={`text-xs ${recognized ? "text-green-700" : "text-foreground-500"}`}>
            {recognized ? "Xarita manzili topildi." : "Google Maps → «Ulashish» → «Xaritani joylashtirish» dagi kodni (yoki undagi src manzilini) shu yerga qo'ying."}
          </p>
          <label className="block text-sm font-medium text-foreground-800">Balandligi (px)
            <input type="number" min={MAP_HEIGHT.min} max={MAP_HEIGHT.max} className={`${FIELD} mt-1 w-32`} value={first.provider === "map" ? first.height : MAP_HEIGHT.default} onChange={(e) => onChange(setEmbedField(data, "height", Number(e.target.value)))} />
          </label>
        </>
      )}
      <label className="block text-sm font-medium text-foreground-800">Nomi ({lang.toUpperCase()}) — ekranni o'qish dasturlari uchun
        <input
          className={`${FIELD} mt-1`}
          value={data[lang].title}
          onChange={(e) => {
            const next = structuredClone(data) as EmbedData;
            next[lang].title = e.target.value;
            onChange(next);
          }}
        />
      </label>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------------------------- document

function DocumentForm({ data, lang, info, onChange }: { data: DocumentData; lang: Lang; info: { title: string; filename: string } | null; onChange: (next: DocumentData) => void }) {
  const style = data.uz.style;
  return (
    <div className="space-y-4">
      {info && <p className="rounded-md bg-background-100 px-3 py-2 text-sm text-foreground-700"><i className="ri-file-text-line mr-1" />Fayl: <strong>{info.filename}</strong> (faylni almashtirish uchun kartani belgilab «Faylni almashtirish» tugmasini bosing)</p>}
      <fieldset>
        <legend className="mb-1.5 text-sm font-medium text-foreground-800">Ko'rinishi (hamma tilda bir xil)</legend>
        <div className="space-y-1.5">
          {DOCUMENT_STYLES.map((option) => (
            <label key={option.value} className="flex cursor-pointer items-start gap-2 rounded-md border border-background-200 p-2.5 text-sm hover:bg-background-100">
              <input type="radio" name="doc-style" className="mt-1" checked={style === option.value} onChange={() => onChange(setDocumentStyle(data, option.value))} />
              <span><strong>{option.label}</strong><br /><span className="text-xs text-foreground-500">{option.hint}</span></span>
            </label>
          ))}
        </div>
      </fieldset>
      <label className="block text-sm font-medium text-foreground-800">Nomi ({lang.toUpperCase()})
        <input className={`${FIELD} mt-1`} value={data[lang].caption} onChange={(e) => onChange(setDocumentCaption(data, lang, e.target.value))} />
      </label>
    </div>
  );
}


// ---------------------------------------------------------------------------------------------------------------- gallery

function GalleryFormView({ data, lang, onChange }: { data: GalleryForm; lang: Lang; onChange: (next: GalleryForm) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [uploading, setUploading] = useState(0);
  const [error, setError] = useState("");

  async function onFiles(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (inputRef.current) inputRef.current.value = "";
    if (!files.length) return;
    setError("");
    setUploading(files.length);
    const uploaded: { path: string; url: string }[] = [];
    let failed = 0;
    for (const file of files) { // one after another: the pictures keep the order the files were chosen in
      try {
        const result = await uploadMedia(file);
        uploaded.push({ path: result.path, url: result.url });
      } catch {
        failed += 1;
      }
      setUploading((n) => n - 1);
    }
    if (uploaded.length) onChange(addPictures(data, uploaded));
    if (failed) setError(`${failed} ta faylni yuklab bo'lmadi.`);
  }

  return (
    <div className="space-y-4">
      <fieldset>
        <legend className="mb-1.5 text-sm font-medium text-foreground-800">Ko'rinishi (hamma tilda bir xil)</legend>
        <div className="grid gap-1.5 sm:grid-cols-3">
          {GALLERY_STYLES.map((option) => (
            <label key={option.value || "default"} className="flex cursor-pointer items-start gap-2 rounded-md border border-background-200 p-2.5 text-sm hover:bg-background-100">
              <input type="radio" name="gallery-style" className="mt-1" checked={data.style === option.value} onChange={() => onChange(setGalleryStyle(data, option.value))} />
              <span><strong>{option.label}</strong><br /><span className="text-xs text-foreground-500">{option.hint}</span></span>
            </label>
          ))}
        </div>
      </fieldset>
      <p className="text-xs text-foreground-500">Rasmlar va ularning tartibi uch tilda bir xil; izoh (alt matn) har til uchun alohida: hozir {lang.toUpperCase()} tilidagisi.</p>
      <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
        {data.pictures.map((picture, index) => (
          <li key={`${picture.image_id ?? picture.path}-${index}`} className="rounded-md border border-background-300 bg-background-100 p-1.5">
            <div className="relative aspect-[4/3] overflow-hidden rounded bg-background-200">
              {picture.url && <img src={picture.url} alt="" className="h-full w-full object-cover" />}
              <span className="absolute left-1 top-1 rounded bg-foreground-950/70 px-1.5 text-[11px] font-semibold text-background-50">{index + 1}</span>
            </div>
            <div className="mt-1 flex justify-between">
              <button type="button" title="Oldinga" aria-label={`${index + 1}-rasmni oldinga`} disabled={index === 0} onClick={() => onChange(movePicture(data, index, -1))} className="h-7 w-7 rounded text-foreground-700 hover:bg-background-200 disabled:opacity-30 cursor-pointer"><i className="ri-arrow-left-s-line" /></button>
              <button type="button" title="Olib tashlash" aria-label={`${index + 1}-rasmni olib tashlash`} onClick={() => onChange(removePicture(data, index))} className="h-7 w-7 rounded text-red-600 hover:bg-red-50 cursor-pointer"><i className="ri-delete-bin-line" /></button>
              <button type="button" title="Orqaga" aria-label={`${index + 1}-rasmni orqaga`} disabled={index === data.pictures.length - 1} onClick={() => onChange(movePicture(data, index, 1))} className="h-7 w-7 rounded text-foreground-700 hover:bg-background-200 disabled:opacity-30 cursor-pointer"><i className="ri-arrow-right-s-line" /></button>
            </div>
            <input aria-label={`${index + 1}-rasm izohi (${lang.toUpperCase()})`} placeholder={`Izoh (${lang.toUpperCase()})`} className={`${FIELD} mt-1 !h-8 text-xs`} value={picture.alt[lang]} onChange={(e) => onChange(setPictureAlt(data, lang, index, e.target.value))} />
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" disabled={uploading > 0} onClick={() => inputRef.current?.click()} className={SMALL_BUTTON}>
          <i className={uploading > 0 ? "ri-loader-4-line animate-spin" : "ri-upload-2-line"} /> Rasm yuklash
        </button>
        <button type="button" onClick={() => setLibraryOpen(true)} className={SMALL_BUTTON}><i className="ri-folder-image-line" /> Kutubxonadan</button>
        {uploading > 0 && <span className="text-xs text-foreground-500">{uploading} ta yuklanmoqda…</span>}
      </div>
      {error && <p role="alert" className="text-xs text-red-600">{error}</p>}
      <input ref={inputRef} type="file" multiple className="hidden" accept=".jpg,.jpeg,.png,.gif,.webp" onChange={onFiles} />
      {libraryOpen && (
        <MediaLibraryModal
          onSelect={(path, url) => { onChange(addPictures(data, [{ path, url }])); setLibraryOpen(false); }}
          onClose={() => setLibraryOpen(false)}
        />
      )}
    </div>
  );
}
