interface Props {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: (e: React.FormEvent) => void;
  placeholder?: string;
  /** "Jami: 239 ta" next to the search box. */
  total?: number;
  loading?: boolean;
}

/** Search box of the list pages: filters as you type (the hook waits a moment after the last key), Enter searches at
 *  once, the cross clears it. */
export default function ListToolbar({ value, onChange, onSubmit, placeholder = "Qidirish...", total, loading }: Props) {
  return (
    <form onSubmit={onSubmit ?? ((e) => e.preventDefault())} className="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2" role="search">
      <div className="relative w-full sm:w-96">
        <i className="ri-search-line pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-foreground-400" aria-hidden="true" />
        <input
          type="search"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          aria-label={placeholder}
          className="h-11 w-full rounded-lg border border-background-300 bg-background-50 pl-10 pr-10 text-sm focus:border-primary-500 focus:outline-none [&::-webkit-search-cancel-button]:hidden"
        />
        {value && (
          <button
            type="button"
            onClick={() => onChange("")}
            className="absolute right-2 top-1/2 flex h-7 w-7 -translate-y-1/2 cursor-pointer items-center justify-center rounded-md text-foreground-400 hover:bg-background-200 hover:text-foreground-700"
            aria-label="Qidiruvni tozalash"
          >
            <i className="ri-close-line" />
          </button>
        )}
      </div>
      {typeof total === "number" && (
        <span className="text-sm text-foreground-500" aria-live="polite">
          {loading ? "Yuklanmoqda..." : `Jami: ${total} ta`}
        </span>
      )}
    </form>
  );
}
