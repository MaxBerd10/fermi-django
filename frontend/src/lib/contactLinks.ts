/**
 * The admin keeps phones and e-mails as one free-text line ("+998 95 062-23-45, +998 95 063-23-45",
 * "info@fjsti.uz, fmioz@mail.ru"). A tel:/mailto: link needs ONE clean value: the first number with its
 * spaces and dashes removed, the first address without the comma after it.
 */
export function telHref(phones: string): string {
  const first = phones.split(/[,;]/)[0] ?? phones;
  const digits = first.replace(/[^\d+]/g, "");
  return `tel:${digits || first.trim()}`;
}

export function mailHref(emails: string): string {
  const first = emails.split(/[\s,;]+/).find((part) => part.includes("@")) ?? emails.trim();
  return `mailto:${first}`;
}
