// Django has no model for the institute-wide "about" blurb this section showed
// (title/body/photo/video for the homepage About block) — there's no Page row
// for it either (confirmed empty), and the admin panel that would manage one is
// out of scope for this integration pass. Rather than fabricate institutional
// copy about a real university, hide the section until real content exists.
export default function About() {
  return null;
}
