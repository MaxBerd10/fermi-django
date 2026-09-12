import { apiClient } from "./client";
import type { GalleryImage } from "../types/content";

// Django's real shape (locale already resolved by the API client). Photos
// are flat and uncaptioned on the old site (every one had an empty title in
// every language), so `caption` is almost always "" — see GalleryPhoto's
// docstring in apps/media_lib/models.py.
interface DjangoImage {
  id: number;
  file: string;
  width: number | null;
  height: number | null;
  alt_text: string;
}
interface DjangoGalleryPhoto {
  id: number;
  image: DjangoImage;
  caption: string;
  order: number;
}

function mapPhoto(photo: DjangoGalleryPhoto): GalleryImage {
  return {
    id: photo.id,
    title: photo.caption,
    img: photo.image.file,
    slug: String(photo.id),
  };
}

export async function listGallery(page = 1) {
  const { data, meta } = await apiClient.get<DjangoGalleryPhoto[]>("gallery", { page });
  return { data: data.map(mapPhoto), meta };
}

export async function getFullGallery(id: number) {
  const { data } = await apiClient.get<DjangoGalleryPhoto>(`gallery/${id}`);
  return mapPhoto(data);
}
