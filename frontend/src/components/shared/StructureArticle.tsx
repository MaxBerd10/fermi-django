import type { ContentBlock } from "@/types/blocks";
import type { PageLayout } from "@/types/content";
import LinkifiedText from "@/blocks/LinkifiedText";
import ArticleBody from "./ArticleBody";

function blockText(block?: ContentBlock): string {
  return block?.block_type === "heading" || block?.block_type === "paragraph"
    ? block.data.text.trim() : "";
}

const organizationLabel = /^(?:tashkilot nomi|наименование организации|название организации|organi[sz]ation name|name of (?:the )?organi[sz]ation)\s*:/iu;
const field = /^([^:\n]{2,48}):\s*(\S[\s\S]*)$/u;
const blockNames = /^(?:bloklar nomi|названия блоков|block names)$/iu;
const creditVolume = /^(?:soatlar|объ[её]м часов|volume of hours).*%/iu;
const rowNumber = /^\d+(?:\.\d+)*\.?$/;
const percent = /^\d+(?:[.,]\d+)?\s*%$/;
const totalLabel = /^(?:jami|итого|всего|total)\s*:?$/iu;
const phoneLabel = /^(?:telefon(?: raqami)?|телефон|phone(?: number)?|tel\.?)$/iu;
const healthOffice = /^([\p{L}ʻʼ‘’\x27-]+(?:\s+[\p{L}ʻʼ‘’\x27-]+)?\s+(?:viloyati|shah(?:ar|ri)|respublikasi)\s+sog[ʻʼ‘’']liqni\s+saqlash\s+(?:(?:bosh\s+)?boshqarmasi|vazirligi)|министерство\s+здравоохранения\s+[^\n]+|ministry\s+of\s+health\s+[^\n]+|(?:главное\s+)?управление\s+здравоохранения\s+[^\n]+|[^\n]+?\s+health(?:care)?\s+(?:department|directorate|administration))(?=\s|$)/iu;

const internationalPhone = /(\+998[\s.\-–‑]*(?:\(\s*\d{2}\s*\)|\d{2})[\s.\-–‑]*\d{3}[\s.\-–‑]*\d{2}[\s.\-–‑]*\d{2})(?!\d)/g;

function PhoneLink({ text }: { text: string }) {
  return <a className="structure-directory-phone" href={`tel:${text.replace(/[^+\d]/g, "")}`}>{text}</a>;
}

function ContactLine({ text }: { text: string }) {
  const parts = text.split(internationalPhone);
  return <>{parts.map((part, index) => index % 2 === 1
    ? <PhoneLink key={index} text={part} />
    : part && <LinkifiedText key={index} text={part} />)}</>;
}

function DirectoryValue({ label, value }: { label: string; value: string }) {
  if (phoneLabel.test(label) && /^\+?[\d() .-]+$/.test(value)) {
    const number = value.replace(/[^+\d]/g, "");
    if (/^\+?\d{7,15}$/.test(number)) return <PhoneLink text={value} />;
  }
  if (/^www\.(?:[a-z\d-]+\.)*[a-z\d-]+\.[a-z]{2,}(?:\/[^\s]*)?$/i.test(value)) {
    return <a href={`https://${value}`} target="_blank" rel="noopener noreferrer">{value}</a>;
  }
  return <ContactLine text={value} />;
}

export default function StructureArticle({ blocks, inlinePdfBlockId, title, layout, regulatory }: {
  blocks: ContentBlock[];
  inlinePdfBlockId?: number;
  title: string;
  layout?: PageLayout;
  regulatory?: boolean;
}) {
  const sections = [];
  const isHealthDirectory = blocks.filter((block) => healthOffice.test(blockText(block))).length >= 2;
  const isCareerFaq = layout === "faq";
  const isConference = layout === "conference";
  let start = 0;

  function flush(end: number) {
    if (start < end) sections.push(<ArticleBody key={blocks[start].id}
      blocks={blocks.slice(start, end)} inlinePdfBlockId={inlinePdfBlockId} documentTitle={title} />);
  }

  for (let index = 0; index < blocks.length; index++) {
    const text = blockText(blocks[index]);
    const office = isHealthDirectory ? healthOffice.exec(text) : null;
    const clause = regulatory && blocks[index].block_type === "paragraph"
      ? /^(\d{1,3}[.)])\s+(\S[\s\S]*)$/u.exec(text) : null;
    const revisionNote = regulatory && (/^\([^\n]*(?:tahririda|tahririga|ma[ʻʼ‘’']lumotlari milliy bazasi|в редакции|as amended)/iu.test(text)
      || /^(?:oldingi tahrirga qarang|см\. предыдущую редакцию|see the previous edition)\.?$/iu.test(text));
    if (clause) {
      flush(index);
      sections.push(
        <p className="regulatory-document__clause" key={blocks[index].id}>
          <span className="regulatory-document__clause-number">{clause[1]}</span>{" "}
          <span><LinkifiedText text={clause[2]} /></span>
        </p>,
      );
      start = index + 1;
    } else if (revisionNote) {
      flush(index);
      sections.push(<p className="regulatory-document__revision" key={blocks[index].id}><LinkifiedText text={text} /></p>);
      start = index + 1;
    } else if (regulatory && blocks[index].block_type === "heading" &&
      /^(?:batafsil|подробнее|read more|details)$/iu.test(text) && blocks[index + 1]?.block_type === "document") {
      flush(index);
      sections.push(<p key={blocks[index].id}><LinkifiedText text={text} /></p>);
      start = index + 1;
    } else if (isCareerFaq && /^(?:\d+[.)]\s*)?(?:savol|вопрос|question)\s*:/iu.test(text)) {
      let end = index + 1;
      while (end < blocks.length && !/^(?:\d+[.)]\s*)?(?:savol|вопрос|question)\s*:/iu.test(blockText(blocks[end]))) end++;
      flush(index);
      const answer = blocks.slice(index + 1, end).map((block): ContentBlock =>
        block.block_type === "heading" && /^(?:javob|ответ|answer)\s*:/iu.test(block.data.text.trim())
          ? { ...block, block_type: "paragraph", data: { text: block.data.text } }
          : block,
      );
      sections.push(
        <section className="structure-directory-card structure-faq" key={blocks[index].id}>
          <h2><LinkifiedText text={text} /></h2>
          <ArticleBody blocks={answer} inlinePdfBlockId={inlinePdfBlockId} documentTitle={title} />
        </section>,
      );
      start = end;
      index = end - 1;
    } else if (blocks[index].block_type === "heading" && /^https?:\/\/[^\s<>]+$/i.test(text)) {
      flush(index);
      sections.push(<p key={blocks[index].id}><LinkifiedText text={text} /></p>);
      start = index + 1;
    } else if (/^(?:o[ʻʼ‘’']zbekiston respublikasining bosh vaziri|премьер-министр республики узбекистан|prime minister of (?:the republic of )?uzbekistan|vazir\b|министр\b|minister\b)/iu.test(text)
      && /^(?:toshkent|ташкент|tashkent)\b/iu.test(blockText(blocks[index + 1]))
      && /\b(?:19|20)\d{2}\b/u.test(blockText(blocks[index + 2]))
      && /^(?:№\s*)?\d+(?:[-–—]\d+)?(?:[-–—]son)?$/iu.test(blockText(blocks[index + 3]))) {
      flush(index);
      sections.push(
        <div className="structure-document-signature" key={blocks[index].id}>
          <p>{text}</p>
          <p>{blocks.slice(index + 1, index + 4).map((block) => (
            <span key={block.id}>{blockText(block)}</span>
          ))}</p>
        </div>,
      );
      index += 3;
      start = index + 1;
    } else if (isConference && text) {
      let end = index;
      while (end < blocks.length && blockText(blocks[end])) end++;
      if (end === index) continue;
      flush(index);
      sections.push(
        <ul className="structure-topic-list" key={blocks[index].id}>
          {blocks.slice(index, end).map((block) => (
            <li key={block.id}><LinkifiedText text={blockText(block)} /></li>
          ))}
        </ul>,
      );
      start = end;
      index = end - 1;
    } else if (office) {
      const lines = [text.slice(office[0].length).trim()].filter(Boolean);
      let end = index + 1;
      while (end < blocks.length) {
        const line = blockText(blocks[end]);
        const nextLine = blockText(blocks[end + 1]);
        if (!line || healthOffice.test(line) || organizationLabel.test(nextLine) ||
            blockNames.test(line) || blockNames.test(nextLine)) break;
        lines.push(line);
        end++;
      }
      flush(index);
      sections.push(
        <section className="structure-directory-card" key={blocks[index].id}>
          <h2>{office[0]}</h2>
          {lines.map((line, lineIndex) => <p key={lineIndex}><ContactLine text={line} /></p>)}
        </section>,
      );
      start = end;
      index = end - 1;
    } else if (text && !field.test(text) && organizationLabel.test(blockText(blocks[index + 1]))) {
      const fields = [];
      let end = index + 1;
      for (; end < blocks.length; end++) {
        const match = field.exec(blockText(blocks[end]));
        if (!match || (end > index + 1 && organizationLabel.test(match[0]))) break;
        const label = match[1].trim();
        const value = match[2].trim();
        if (end !== index + 1 || value !== text) fields.push({ id: blocks[end].id, label, value });
      }
      flush(index);
      sections.push(
        <section className="structure-directory-card" key={blocks[index].id}>
          <h2>{text}</h2>
          {fields.length > 0 && <dl>
            {fields.map(({ id, label, value }) => (
              <div key={id}>
                <dt>{label}</dt>
                <dd><DirectoryValue label={label} value={value} /></dd>
              </div>
            ))}
          </dl>}
        </section>,
      );
      start = end;
      index = end - 1;
    } else if (blockNames.test(text) && creditVolume.test(blockText(blocks[index + 1]))) {
      const rows = [];
      let end = index + 2;
      const volume = blockText(blocks[index + 1]);
      while (end < blocks.length) {
        const cell = blockText(blocks[end]);
        const next = blockText(blocks[end + 1]);
        const value = blockText(blocks[end + 2]);
        if (rowNumber.test(cell) && next && percent.test(value)) {
          rows.push(<tr key={blocks[end].id}><td>{cell}</td><th scope="row">{next}</th><td>{value}</td></tr>);
          end += 3;
        } else if (rows.length && /^(?:shu jumladan|в том числе|including)[,:]?$/iu.test(cell)) {
          rows.push(<tr key={blocks[end].id}><td colSpan={3}>{cell}</td></tr>);
          end++;
        } else break;
      }
      if (!rows.length) continue;
      const total = blockText(blocks[end]);
      const totalValue = blockText(blocks[end + 1]);
      const previous = index > start ? blockText(blocks[index - 1]) : "";
      const numberHeader = /^(?:t\s*\/\s*r|№(?:\s*п\s*\/\s*п)?|no\.?)$/iu.test(previous) ? previous : "";
      flush(numberHeader ? index - 1 : index);
      sections.push(
        <div className="structure-credit-table" key={blocks[index].id}>
          <table>
            <thead><tr><th scope="col">{numberHeader || "№"}</th><th scope="col">{text}</th><th scope="col">{volume}</th></tr></thead>
            <tbody>{rows}</tbody>
            {totalLabel.test(total) && percent.test(totalValue) && (
              <tfoot><tr><th scope="row" colSpan={2}>{total}</th><td>{totalValue}</td></tr></tfoot>
            )}
          </table>
        </div>,
      );
      if (totalLabel.test(total) && percent.test(totalValue)) end += 2;
      start = end;
      index = end - 1;
    }
  }
  flush(blocks.length);
  return <>{sections}</>;
}
