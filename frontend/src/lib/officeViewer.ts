const OFFICE_EXTENSION_RE = /^(docx?|xlsx?|pptx?)$/i;

/**
 * Word, Excel and PowerPoint files never show in a browser tab, so their card only offered "download".
 * Microsoft's free viewer can open a public file by its address ("open in the browser"); the file is read
 * by the viewer only when a visitor clicks the button. Returns null for a file the viewer cannot reach
 * (a local or non-https address), and the card then keeps only "download".
 */
export function officeViewerUrl(href: string, extension: string): string | null {
  if (!OFFICE_EXTENSION_RE.test(extension) || typeof window === "undefined") return null;
  try {
    const url = new URL(href, window.location.origin);
    const isPublic = url.protocol === "https:" && !/^(localhost|127\.|\[::1\])/.test(url.hostname);
    return isPublic ? `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(url.href)}` : null;
  } catch {
    return null;
  }
}
