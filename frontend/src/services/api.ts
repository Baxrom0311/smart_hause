import axios, { AxiosError } from "axios";
import type {
  Anomaly,
  AnomalyDetectionRequest,
  AnomalyDetectionResponse,
  AnomalyStats,
  DashboardSummary,
  DataSource,
  DataStats,
  ModelStatus,
  SampleDataset,
  SampleImportRequest,
  SensorData,
  TrainingRequest,
  TrainingResponse,
  UploadResponse,
} from "./types";

const baseURL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";

// The configured base may end with /api or be a host root. We normalize so we can call /api/* and /health uniformly.
const root = baseURL.replace(/\/api\/?$/, "").replace(/\/$/, "");

export const apiClient = axios.create({
  baseURL: root || "",
  timeout: 60000,
});

type ApiErrorBody = {
  detail?: unknown;
};

export function getApiErrorMessage(err: unknown, fallback = "Noma'lum xatolik yuz berdi"): string {
  if (axios.isAxiosError(err)) {
    const ax = err as AxiosError<ApiErrorBody>;
    const detail = ax.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      if (typeof first === "string") return first;
      if (first && typeof first === "object" && "msg" in first) return String(first.msg);
    }
    if (ax.message) return ax.message;
  }
  if (err instanceof Error) return err.message;
  return fallback;
}

async function downloadBlob(url: string, params: Record<string, unknown>, fallbackName: string) {
  const res = await apiClient.get(url, { params, responseType: "blob" });
  const cd = res.headers["content-disposition"] as string | undefined;
  let filename = fallbackName;
  if (cd) {
    const m = /filename\*?=(?:UTF-8'')?["']?([^"';\n]+)["']?/i.exec(cd);
    if (m?.[1]) filename = decodeURIComponent(m[1]);
  }
  const blob = new Blob([res.data], { type: "text/csv" });
  const blobUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
}

// Defensive helpers — backend may occasionally return wrapped or unexpected shapes.
function toArray<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    if (Array.isArray(obj.items)) return obj.items as T[];
    if (Array.isArray(obj.data)) return obj.data as T[];
    if (Array.isArray(obj.results)) return obj.results as T[];
  }
  return [];
}

function toListResponse<T>(data: unknown): { total: number; items: T[] } {
  if (data && typeof data === "object" && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>;
    const items = toArray<T>(obj.items ?? data);
    const total = typeof obj.total === "number" ? obj.total : items.length;
    return { total, items };
  }
  const items = toArray<T>(data);
  return { total: items.length, items };
}

function toRecord(data: unknown): Record<string, unknown> {
  return data && typeof data === "object" ? (data as Record<string, unknown>) : {};
}

function toNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function toNumberArray(value: unknown): number[] {
  return Array.isArray(value) ? value.filter((item): item is number => typeof item === "number") : [];
}

function normalizeStatus(data: unknown): ModelStatus {
  const obj = toRecord(data);
  return {
    state: (typeof obj.state === "string" ? obj.state : "idle") as ModelStatus["state"],
    sensor_type: typeof obj.sensor_type === "string" ? obj.sensor_type : null,
    source_file: typeof obj.source_file === "string" ? obj.source_file : null,
    message: typeof obj.message === "string" ? obj.message : null,
    started_at: typeof obj.started_at === "string" ? obj.started_at : null,
    finished_at: typeof obj.finished_at === "string" ? obj.finished_at : null,
    training_id: toNumber(obj.training_id),
    progress: toNumber(obj.progress) ?? 0,
    current_epoch: toNumber(obj.current_epoch),
    total_epochs: toNumber(obj.total_epochs),
    train_loss: toNumber(obj.train_loss),
    val_loss: toNumber(obj.val_loss),
    loss_history: toNumberArray(obj.loss_history),
    val_loss_history: toNumberArray(obj.val_loss_history),
  };
}

export const api = {
  // Health
  health: () => apiClient.get<{ status?: string }>("/health").then((r) => r.data),

  // Data
  listSamples: () =>
    apiClient.get("/api/data/samples").then((r) => toArray<SampleDataset>(r.data)),
  importSample: (body: SampleImportRequest) =>
    apiClient.post<UploadResponse>("/api/data/import-sample", body).then((r) => r.data),
  uploadCsv: (file: File, sensor_type?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (sensor_type) fd.append("sensor_type", sensor_type);
    return apiClient
      .post<UploadResponse>("/api/data/upload", fd, { headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },
  listData: (params: { sensor_type?: string; source_file?: string; limit?: number; offset?: number } = {}) =>
    apiClient.get("/api/data/list", { params }).then((r) => toListResponse<SensorData>(r.data)),
  stats: (params: { sensor_type?: string; source_file?: string } = {}) =>
    apiClient.get<DataStats>("/api/data/stats", { params }).then((r) => r.data),
  sources: (sensor_type?: string) =>
    apiClient
      .get("/api/data/sources", { params: sensor_type ? { sensor_type } : {} })
      .then((r) => toArray<DataSource>(r.data)),
  sensors: () => apiClient.get("/api/data/sensors").then((r) => toArray<string>(r.data)),
  deleteSource: (source_file: string, sensor_type?: string) =>
    apiClient
      .delete(`/api/data/source/${encodeURIComponent(source_file)}`, {
        params: sensor_type ? { sensor_type } : {},
      })
      .then((r) => r.data),
  deleteSensor: (sensor_type: string) =>
    apiClient.delete(`/api/data/${encodeURIComponent(sensor_type)}`).then((r) => r.data),
  exportData: (params: { sensor_type?: string; source_file?: string } = {}) =>
    downloadBlob("/api/data/export", params, "sensor_data.csv"),

  // Model
  train: (body: TrainingRequest) =>
    apiClient.post<ModelStatus>("/api/model/train", body).then((r) => normalizeStatus(r.data)),
  status: () => apiClient.get<ModelStatus>("/api/model/status").then((r) => normalizeStatus(r.data)),
  history: () =>
    apiClient.get("/api/model/history").then((r) => toArray<TrainingResponse>(r.data)),
  historyDetail: (id: number) =>
    apiClient.get<TrainingResponse>(`/api/model/history/${id}`).then((r) => r.data),

  // Anomaly
  detect: (body: AnomalyDetectionRequest) =>
    apiClient.post<AnomalyDetectionResponse>("/api/anomaly/detect", body).then((r) => r.data),
  results: (params: { sensor_type?: string; source_file?: string; limit?: number; offset?: number } = {}) =>
    apiClient.get("/api/anomaly/results", { params }).then((r) => toListResponse<Anomaly>(r.data)),
  resultDetail: (id: number) => apiClient.get<Anomaly>(`/api/anomaly/results/${id}`).then((r) => r.data),
  anomalyStats: () => apiClient.get<AnomalyStats>("/api/anomaly/stats").then((r) => r.data),
  exportAnomalies: (params: { sensor_type?: string; source_file?: string; anomaly_only?: boolean } = {}) =>
    downloadBlob("/api/anomaly/export", params, "anomalies.csv"),

  // Dashboard
  dashboard: () => apiClient.get<DashboardSummary>("/api/dashboard/summary").then((r) => r.data),

};

export type Api = typeof api;
