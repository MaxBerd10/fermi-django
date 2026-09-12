import { apiClient } from "./client";
import type { DepartmentDetail, DepartmentListItem, Leader } from "../types/content";
import { blocksToPlainText } from "@/lib/blocksToText";
import type { ContentBlock } from "../types/blocks";

// Django's real shapes (locale already resolved by the API client — see
// resolveLocale in client.ts — so `name`/`full_name`/etc. below are plain
// strings, not {uz,ru,en} records).
interface DjangoImage {
  id: number;
  file: string;
  width: number | null;
  height: number | null;
  alt_text: string;
}
interface DjangoStaffMember {
  id: number;
  full_name: string;
  title: string;
  bio: string;
  activity: string;
  photo: DjangoImage | null;
  is_head: boolean;
  order: number;
  phone: string;
  email: string;
  reception_days: string;
}
interface DjangoDepartmentListItem {
  id: number;
  slug: string;
  name: string;
  logo: DjangoImage | null;
}
interface DjangoDepartmentDetail extends DjangoDepartmentListItem {
  page: { id: number; slug: string; blocks: ContentBlock[] };
  staff: DjangoStaffMember[];
}

function mapStaffToLeader(staff: DjangoStaffMember): Leader {
  return {
    id: staff.id,
    name: staff.full_name,
    position: staff.title,
    activity: staff.activity,
    biography: staff.bio,
    receptionDays: staff.reception_days,
    phone: staff.phone,
    faks: null, // Django's StaffMember has no fax field — the old CMS's was unused everywhere it mattered.
    email: staff.email,
    photo: staff.photo?.file ?? "",
  };
}

function mapListItem(dept: DjangoDepartmentListItem): DepartmentListItem {
  return {
    title: dept.name,
    img: dept.logo?.file ?? "",
    slug: dept.slug,
  };
}

function mapDetail(dept: DjangoDepartmentDetail): DepartmentDetail {
  return {
    id: dept.id,
    title: dept.name,
    img: dept.logo?.file ?? "",
    slug: dept.slug,
    content: blocksToPlainText(dept.page.blocks),
    blocks: dept.page.blocks,
    menu: null, // Django has no per-department menu-branch concept — nav comes from apps.menu instead (see api/menu.ts).
    leaders: dept.staff.map(mapStaffToLeader),
  };
}

export async function listDepartments() {
  const { data } = await apiClient.get<DjangoDepartmentListItem[]>("departments");
  return data.map(mapListItem);
}

export async function getDepartment(slug: string, _menuId?: number) {
  const { data } = await apiClient.get<DjangoDepartmentDetail>(`departments/${slug}`);
  return mapDetail(data);
}
