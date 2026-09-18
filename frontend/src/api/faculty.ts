import { apiClient } from "./client";
import type { FacultyDetail, FacultyListItem, Leader } from "../types/content";
import { blocksToPlainText } from "@/lib/blocksToText";
import type { ContentBlock } from "../types/blocks";

// Same Django shapes as api/departments.ts — see that file's comments.
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
interface DjangoFacultyListItem {
  id: number;
  slug: string;
  name: string;
  logo: DjangoImage | null;
  order: number;
}
interface DjangoFacultyDetail extends DjangoFacultyListItem {
  page: { id: number; slug: string; blocks: ContentBlock[] };
  leaders: DjangoStaffMember[];
}

function mapStaffToLeader(staff: DjangoStaffMember): Leader {
  return {
    id: staff.id,
    name: staff.full_name,
    position: staff.title,
    isHead: staff.is_head,
    activity: staff.activity,
    biography: staff.bio,
    receptionDays: staff.reception_days,
    phone: staff.phone,
    faks: null,
    email: staff.email,
    photo: staff.photo?.file ?? "",
  };
}

function mapListItem(faculty: DjangoFacultyListItem): FacultyListItem {
  return {
    id: faculty.id,
    title: faculty.name,
    img: faculty.logo?.file ?? "",
    slug: faculty.slug,
  };
}

function mapDetail(faculty: DjangoFacultyDetail): FacultyDetail {
  return {
    id: faculty.id,
    title: faculty.name,
    img: faculty.logo?.file ?? "",
    slug: faculty.slug,
    content: blocksToPlainText(faculty.page.blocks),
    blocks: faculty.page.blocks,
    menu: null,
    leaders: faculty.leaders.map(mapStaffToLeader),
  };
}

export async function listFaculty() {
  // Django registers this resource as "faculties" (plural), not "faculty".
  const { data } = await apiClient.get<DjangoFacultyListItem[]>("faculties");
  return data.map(mapListItem);
}

export async function getFaculty(slug: string, _menuId?: number) {
  const { data } = await apiClient.get<DjangoFacultyDetail>(`faculties/${slug}`);
  return mapDetail(data);
}
