import { files, keywordHits, metaItems, orders, rankRows, topMetrics } from "@/data/mock";

export async function mockDelay<T>(data: T, delay = 220): Promise<T> {
  await new Promise((resolve) => window.setTimeout(resolve, delay));
  return data;
}

export function getDashboardMetrics() {
  return mockDelay(topMetrics);
}

export function createMockTask() {
  return mockDelay({
    task_no: "T202606250001",
    mode: "multi",
    status: "queued",
    b_file_count: 3,
    expires_at: "2026-07-02T10:00:00+08:00"
  });
}

export function getMockSummary() {
  return mockDelay({
    task_no: "T202606250001",
    files,
    rankRows,
    metaItems,
    keywordHits
  });
}

export function getMockOrders() {
  return mockDelay(orders);
}
