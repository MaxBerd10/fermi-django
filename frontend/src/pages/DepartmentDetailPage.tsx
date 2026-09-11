import { useParams } from "react-router-dom";
import { DepartmentPage } from "../DepartmentPage";

export function DepartmentDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  if (!slug) return null;
  return <DepartmentPage slug={slug} />;
}
