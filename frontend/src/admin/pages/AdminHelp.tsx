import { useState } from "react";
import content from "../help/helpContent.json";

type Block =
  | { type: "p"; text: string }
  | { type: "steps"; title: string; items: string[] }
  | { type: "warn"; title: string; items: string[] }
  | { type: "tip"; title: string; items: string[] }
  | { type: "table"; head: string[]; rows: string[][] };

interface Section {
  id: string;
  title: string;
  blocks: Block[];
}

const SECTIONS = content.sections as Section[];

function Callout({ tone, title, items }: { tone: "warn" | "tip"; title: string; items: string[] }) {
  const palette =
    tone === "warn"
      ? "border-amber-300 bg-amber-50 text-amber-900"
      : "border-primary-200 bg-primary-50 text-primary-900";
  return (
    <div className={`rounded-lg border px-4 py-3 ${palette}`}>
      <p className="mb-1.5 flex items-center gap-2 text-sm font-semibold">
        <i className={tone === "warn" ? "ri-error-warning-line" : "ri-information-line"} aria-hidden="true" />
        {title}
      </p>
      <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function renderBlock(block: Block, index: number) {
  switch (block.type) {
    case "p":
      return (
        <p key={index} className="text-sm leading-relaxed text-foreground-800">
          {block.text}
        </p>
      );
    case "steps":
      return (
        <div key={index}>
          <p className="mb-2 text-sm font-semibold text-foreground-900">{block.title}</p>
          <ol className="space-y-2">
            {block.items.map((item, i) => (
              <li key={item} className="flex gap-3 text-sm leading-relaxed text-foreground-800">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary-500 text-xs font-bold text-background-50">
                  {i + 1}
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ol>
        </div>
      );
    case "warn":
    case "tip":
      return <Callout key={index} tone={block.type} title={block.title} items={block.items} />;
    case "table":
      return (
        <div key={index} className="overflow-x-auto rounded-lg border border-background-200">
          <table className="w-full text-left text-sm">
            <thead className="bg-background-100 text-xs uppercase tracking-wide text-foreground-500">
              <tr>
                {block.head.map((h) => (
                  <th key={h} className="px-3 py-2 font-semibold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {block.rows.map((row) => (
                <tr key={row[0]} className="border-t border-background-200 align-top">
                  {row.map((cell, i) => (
                    <td key={i} className={`px-3 py-2 leading-relaxed ${i === 0 ? "font-medium text-foreground-900" : "text-foreground-700"}`}>
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
  }
}

/** The staff handbook, inside the panel itself (the same text is exported to the printable PDF). */
export default function AdminHelp() {
  const [open, setOpen] = useState<string>(SECTIONS[0].id);

  return (
    <div className="max-w-4xl">
      <h1 className="font-heading text-2xl font-bold text-foreground-950">{content.title}</h1>
      <p className="mt-1 mb-6 text-sm text-foreground-600">{content.subtitle}</p>

      <div className="grid gap-6 lg:grid-cols-[14rem_minmax(0,1fr)]">
        <nav aria-label="Qoʻllanma boʻlimlari" className="lg:sticky lg:top-4 lg:self-start">
          <ul className="space-y-1">
            {SECTIONS.map((section) => (
              <li key={section.id}>
                <button
                  type="button"
                  onClick={() => {
                    setOpen(section.id);
                    document.getElementById(`help-${section.id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
                  }}
                  className={`w-full cursor-pointer rounded-md px-3 py-2 text-left text-sm transition-colors ${
                    open === section.id ? "bg-primary-500 font-semibold text-background-50" : "text-foreground-700 hover:bg-background-200"
                  }`}
                >
                  {section.title}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <div className="space-y-8">
          {SECTIONS.map((section) => (
            <section key={section.id} id={`help-${section.id}`} className="scroll-mt-4 rounded-xl border border-background-200 bg-background-50 p-5">
              <h2 className="mb-4 font-heading text-lg font-bold text-foreground-950">{section.title}</h2>
              <div className="space-y-4">{section.blocks.map(renderBlock)}</div>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
