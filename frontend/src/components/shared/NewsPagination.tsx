import { useSearchParams } from "react-router-dom";
import Paginator from "./Paginator";

/** The news/gallery/video lists keep the current page in the URL (?page=N) so a page can be linked to. */
export default function NewsPagination({ page, totalPages }: { page: number; totalPages: number }) {
  const [, setSearchParams] = useSearchParams();
  return <Paginator page={page} totalPages={totalPages} onChange={(p) => setSearchParams({ page: String(p) })} />;
}
