// Shaped to match what DRF's PageNumberPagination actually returns
// ({count, next, previous, results}) — `total` is DRF's `count` renamed so
// every existing `res.meta?.total` call site needs no change. `next`/
// `previous` are the raw page URLs DRF gives back; unused today but kept
// for a future "load more"/pager UI.
export interface ApiMeta {
  total: number;
  next: string | null;
  previous: string | null;
}

export class ApiError extends Error {
  code: string;
  status: number;
  fields?: Record<string, string[]>;

  constructor(message: string, code: string, status: number, fields?: Record<string, string[]>) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.fields = fields;
  }
}
