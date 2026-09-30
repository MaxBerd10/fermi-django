import { useRef, useState } from "react";
import { mediaUrl, uploadMedia } from "@/api/admin";
import MediaLibraryModal from "./MediaLibraryModal";

interface GalleryPickerProps {
  label: string;
  value: string[] | null | undefined;
  onChange: (paths: string[]) => void;
}

/** MediaPicker's multi-image sibling: upload several files at once (or pick from the library), reorder and remove them. Emits the same path/URL strings MediaPicker does. */
export default function GalleryPicker({ label, value, onChange }: GalleryPickerProps) {
  const items = value ?? [];
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(0);
  const [error, setError] = useState("");
  const [libraryOpen, setLibraryOpen] = useState(false);

  async function onFilesSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (inputRef.current) inputRef.current.value = "";
    if (files.length === 0) return;
    setError("");
    setUploading(files.length);
    const uploaded: string[] = [];
    let failed = 0;
    // Sequential keeps the gallery in the order the files were chosen.
    for (const file of files) {
      try {
        const result = await uploadMedia(file);
        uploaded.push(result.path);
      } catch {
        failed += 1;
      }
      setUploading((n) => n - 1);
    }
    if (uploaded.length) onChange([...items, ...uploaded]);
    if (failed) setError(`${failed} ta faylni yuklab bo'lmadi.`);
  }

  function move(index: number, delta: number) {
    const next = [...items];
    const [item] = next.splice(index, 1);
    next.splice(index + delta, 0, item);
    onChange(next);
  }

  return (
    <div>
      <label className="block text-sm font-medium text-foreground-700 mb-1.5">
        {label} {items.length > 0 && <span className="text-foreground-500 font-normal">({items.length})</span>}
      </label>

      {items.length > 0 && (
        <ul className="grid grid-cols-3 sm:grid-cols-5 gap-3 mb-3">
          {items.map((path, i) => (
            <li key={`${path}-${i}`} className="relative group aspect-square rounded-md overflow-hidden border border-background-300 bg-background-100">
              <img src={mediaUrl(path) ?? ""} alt="" className="w-full h-full object-cover" />
              <div className="absolute inset-x-0 bottom-0 flex justify-between gap-1 p-1 bg-foreground-950/60 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
                <button type="button" disabled={i === 0} onClick={() => move(i, -1)} title="Chapga" className="w-7 h-7 flex items-center justify-center rounded text-background-50 hover:bg-background-50/20 disabled:opacity-30 cursor-pointer">
                  <i className="ri-arrow-left-s-line" />
                </button>
                <button type="button" onClick={() => onChange(items.filter((_, j) => j !== i))} title="Olib tashlash" className="w-7 h-7 flex items-center justify-center rounded text-background-50 hover:bg-accent-600 cursor-pointer">
                  <i className="ri-delete-bin-line" />
                </button>
                <button type="button" disabled={i === items.length - 1} onClick={() => move(i, 1)} title="O'ngga" className="w-7 h-7 flex items-center justify-center rounded text-background-50 hover:bg-background-50/20 disabled:opacity-30 cursor-pointer">
                  <i className="ri-arrow-right-s-line" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={uploading > 0}
          onClick={() => inputRef.current?.click()}
          className="h-10 px-4 rounded-md border border-background-300 text-sm font-medium text-foreground-700 hover:bg-background-100 cursor-pointer disabled:opacity-60 flex items-center gap-2"
        >
          {uploading > 0 ? (
            <i className="ri-loader-4-line w-4 h-4 flex items-center justify-center animate-spin" />
          ) : (
            <i className="ri-upload-2-line w-4 h-4 flex items-center justify-center" />
          )}
          {uploading > 0 ? `Yuklanmoqda (${uploading})...` : "Rasmlar yuklash"}
        </button>
        <button
          type="button"
          onClick={() => setLibraryOpen(true)}
          className="h-10 px-4 rounded-md border border-background-300 text-sm font-medium text-foreground-700 hover:bg-background-100 cursor-pointer flex items-center gap-2"
        >
          <i className="ri-folder-image-line w-4 h-4 flex items-center justify-center" />
          Kutubxonadan
        </button>
        {items.length > 1 && (
          <button type="button" onClick={() => onChange([])} className="text-sm text-foreground-500 hover:text-accent-600 cursor-pointer">
            Hammasini olib tashlash
          </button>
        )}
      </div>
      <p className="mt-1.5 text-xs text-foreground-500">Bir nechta rasmni birdaniga tanlash mumkin. Ular yangilik matni ostida galereya bo'lib chiqadi.</p>
      <input ref={inputRef} type="file" multiple className="hidden" onChange={onFilesSelected} accept=".jpg,.jpeg,.png,.gif,.webp" />
      {error && <p className="mt-1 text-xs text-accent-600">{error}</p>}
      {libraryOpen && (
        <MediaLibraryModal
          onSelect={(path) => {
            onChange([...items, path]);
            setLibraryOpen(false);
          }}
          onClose={() => setLibraryOpen(false)}
        />
      )}
    </div>
  );
}
