import { ApiError } from "@/types/api";

/** The record asked for does not exist (it was removed, hidden as a draft, or the link is mistyped). */
export function isNotFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}
