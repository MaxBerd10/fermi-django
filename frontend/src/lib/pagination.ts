/**
 * How many items one page of a list endpoint holds. It must equal DRF's PAGE_SIZE in config/settings.py:
 * the pagers work out the number of pages as count / this. With a smaller number here than the server's
 * (9 vs 20) the pager offered pages that do not exist and the last ones answered "Invalid page" (404).
 */
export const API_PAGE_SIZE = 20;
