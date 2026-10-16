const MAX_SIDE = 2000;
const THUMB_SIDE = 240;

async function bitmapOf(file: Blob): Promise<ImageBitmap> {
  // `from-image` applies the camera's rotation, so a phone photo is not uploaded sideways
  return createImageBitmap(file, { imageOrientation: "from-image" } as ImageBitmapOptions);
}

function draw(bitmap: ImageBitmap, longest: number): HTMLCanvasElement {
  const scale = Math.min(1, longest / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(bitmap.width * scale));
  canvas.height = Math.max(1, Math.round(bitmap.height * scale));
  canvas.getContext("2d")?.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  return canvas;
}

/** A phone photo is often 5-10 MB: shrink it to 2000 px / JPEG before it travels over a mobile network (the server
 *  checks and re-encodes it again). Anything the browser cannot decode is sent as it is. Also returns a small preview
 *  as a data: address (the page's security policy allows data: images, not blob: ones). */
export async function prepareImage(file: File): Promise<{ blob: Blob; preview: string }> {
  try {
    const bitmap = await bitmapOf(file);
    const full = draw(bitmap, MAX_SIDE);
    const blob = await new Promise<Blob | null>((resolve) => full.toBlob(resolve, "image/jpeg", 0.86));
    const preview = draw(bitmap, THUMB_SIDE).toDataURL("image/jpeg", 0.7);
    bitmap.close();
    if (blob) return { blob, preview };
  } catch {
    /* fall through */
  }
  return { blob: file, preview: "" };
}
