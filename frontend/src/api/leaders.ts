import i18n from "@/i18n";
import { apiClient } from "./client";
import type { Leader, LeadersResponse } from "../types/content";

// Django's real shape (locale already resolved by the API client — see
// resolveLocale in client.ts) — see api/departments.ts's DjangoStaffMember
// for the identical underlying StaffMemberSerializer output.
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
interface DjangoLeadersResponse {
  category: { id: string; title: string };
  menu: null;
  leaders: DjangoStaffMember[];
}

function mapLeader(staff: DjangoStaffMember): Leader {
  // The legacy import assigned a department event photo and report text to
  // Karimova's record. Keep CMS edits authoritative once that asset is replaced.
  const hasKarimovaImport = staff.id === 460 && staff.photo?.id === 5650;
  return {
    id: staff.id,
    name: staff.full_name,
    position: staff.title,
    isHead: staff.is_head,
    activity: staff.activity,
    biography: hasKarimovaImport ? i18n.t("leader.bio.karimova") : staff.bio,
    receptionDays: staff.reception_days,
    phone: staff.phone,
    faks: null, // Django's StaffMember has no fax field — the old CMS's was unused everywhere it mattered.
    email: staff.email,
    photo: hasKarimovaImport
      ? "https://fjsti.uz/uploads/img/kafedra/Endokrinologiya/image_1_1769238169986.jpg"
      : staff.photo?.file ?? "",
  };
}

export async function getLeaders(categorySlug: string, _menuId?: number): Promise<LeadersResponse> {
  const { data } = await apiClient.get<DjangoLeadersResponse>(`leaders/${categorySlug}`);
  return {
    category: data.category,
    menu: data.menu,
    leaders: data.leaders.map(mapLeader),
  };
}
