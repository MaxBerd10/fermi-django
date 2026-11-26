import ArticleBody from "./ArticleBody";
import StructureArticle from "./StructureArticle";
import type { ContentBlock } from "@/types/blocks";

function isPreamble(block: ContentBlock): boolean {
  if (block.block_type === "heading") return true;
  if (block.block_type !== "paragraph") return false;
  const text = block.data.text.trim();
  return /^[[(]/.test(text) || (text === text.toLocaleUpperCase() && /\p{L}/u.test(text));
}

export default function RegulatoryDocument({ blocks, inlinePdfBlockId, title }: {
  blocks: ContentBlock[];
  inlinePdfBlockId?: number;
  title: string;
}) {
  const first = blocks[0];
  const openingTitle = first?.block_type === "paragraph" && /^(?:o[ʻʼ‘’']zbekiston respublikasi qonuni|закон республики узбекистан|law of (?:the )?republic of uzbekistan)\s+[«“"]/iu.test(first.data.text.trim())
    ? first.data.text.trim() : undefined;
  const content = openingTitle ? blocks.slice(1).filter((block) =>
    block.block_type !== "heading" || block.data.text.trim() !== openingTitle,
  ) : blocks;
  const end = content.findIndex((block) => !isPreamble(block));
  const preambleEnd = end < 0 ? content.length : end;
  const body = content.slice(preambleEnd).map((block): ContentBlock => {
    if (openingTitle && block.block_type === "paragraph" && block.data.text.length <= 160 &&
        /^(?:o[ʻʼ‘’']zbekiston respublikasi prezidentining|указ президента|decree of the president).+\d+/iu.test(block.data.text.trim())) {
      return { ...block, block_type: "heading", data: { text: block.data.text.trim() } };
    }
    if (inlinePdfBlockId === undefined || block.block_type !== "paragraph") return block;
    const text = block.data.text.replace(/^\s*yuklab olish uchun bosing\s*>+\s*/iu, "");
    return text && text !== block.data.text ? { ...block, data: { ...block.data, text } } : block;
  });
  return (
    <div className="regulatory-document">
      {openingTitle && <h2>{openingTitle}</h2>}
      {preambleEnd > 0 && (
        <div className="regulatory-document__preamble">
          <ArticleBody blocks={content.slice(0, preambleEnd)} />
        </div>
      )}
      <StructureArticle blocks={body} inlinePdfBlockId={inlinePdfBlockId} title={title} regulatory />
    </div>
  );
}
