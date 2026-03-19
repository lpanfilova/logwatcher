// API client for LogWatcher backend integration
import axios from "axios";

const API_BASE_URL = "/api"; // Proxied to backend
const AUTH_STORAGE_KEY = "logwatcher-authenticated";

export interface LogEntry {
  id: string;
  timestamp: string;
  message: string;
  service: string;
  source: string;
  level: number;
  event?: string;
  msg?: string;
}

export interface SummaryData {
  total_logs: number;
  services: Array<{ name: string; count: number }>;
  sources: Array<{ name: string; count: number }>;
  time_range: {
    oldest: string;
    newest: string;
  };
}

export interface TimelineData {
  interval: string;
  data: Array<{ timestamp: string; count: number }>;
}

export interface ByEventData {
  events: Array<{ event: string; count: number }>;
}

export interface LogVolumeData {
  interval: string;
  data: Array<{
    timestamp: string;
    total: number;
    by_level: Record<string, number>;
  }>;
}

export interface ErrorMetricsData {
  interval: string;
  total_errors: number;
  data: Array<{ timestamp: string; count: number }>;
}

export interface TopErrorsData {
  top_errors: Array<{ event: string; count: number }>;
}

export interface LogsResponse {
  total: number;
  logs: LogEntry[];
}

export interface LogsQueryParams {
  q?: string;
  size?: number;
  service?: string;
  source?: string;
  level?: number;
  min_level?: number;
  event?: string;
}

export interface TimelineQueryParams {
  interval?: string;
  service?: string;
  source?: string;
}

export class ApiClient {
  private axiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
  });

  async login(username: string, password: string): Promise<void> {
    await this.axiosInstance.post("/authenticate", { username, password });
  }

  // Get dashboard summary statistics
  async getSummary(): Promise<SummaryData> {
    const response = await this.axiosInstance.get("/summary");
    return response.data;
  }

  // Get timeline metrics for charts
  async getTimelineMetrics(
    interval: string = "1h",
    service?: string,
  ): Promise<TimelineData> {
    const params = new URLSearchParams();
    params.append("interval", interval);
    if (service) params.append("service", service);

    const response = await this.axiosInstance.get(
      `/metrics/timeline?${params}`,
    );
    return response.data;
  }

  // Get counts grouped by event type
  async getMetricsByEvent(): Promise<ByEventData> {
    const response = await this.axiosInstance.get("/metrics/by-event");
    return response.data;
  }

  // Get log volume over time with level breakdown
  async getLogVolumeMetrics(
    interval: string = "1h",
    service?: string,
  ): Promise<LogVolumeData> {
    const params = new URLSearchParams();
    params.append("interval", interval);
    if (service) params.append("service", service);

    const response = await this.axiosInstance.get(
      `/metrics/log-volume?${params}`,
    );
    return response.data;
  }

  // Get error trend metrics
  async getErrorMetrics(
    interval: string = "1h",
    service?: string,
  ): Promise<ErrorMetricsData> {
    const params = new URLSearchParams();
    params.append("interval", interval);
    if (service) params.append("service", service);

    const response = await this.axiosInstance.get(`/metrics/errors?${params}`);
    return response.data;
  }

  // Get most frequent errors
  async getTopErrorsMetrics(
    size: number = 10,
    service?: string,
  ): Promise<TopErrorsData> {
    const params = new URLSearchParams();
    params.append("size", size.toString());
    if (service) params.append("service", service);

    const response = await this.axiosInstance.get(
      `/metrics/top-errors?${params}`,
    );
    return response.data;
  }

  // Search and filter logs
  async getLogs(params?: LogsQueryParams): Promise<LogsResponse> {
    const queryParams = new URLSearchParams();
    if (params?.q) queryParams.append("q", params.q);
    if (params?.size) queryParams.append("size", params.size.toString());
    if (params?.service) queryParams.append("service", params.service);
    if (params?.source) queryParams.append("source", params.source);
    if (params?.level !== undefined)
      queryParams.append("level", params.level.toString());
    if (params?.min_level !== undefined)
      queryParams.append("min_level", params.min_level.toString());
    if (params?.event) queryParams.append("event", params.event);

    const response = await this.axiosInstance.get(`/logs?${queryParams}`);
    return response.data;
  }

  // Get single log by ID
  async getLogById(id: string): Promise<LogEntry> {
    const response = await this.axiosInstance.get(`/logs/${id}`);
    return response.data.log;
  }
}

export const apiClient = new ApiClient();

export const isAuthenticated = (): boolean => {
  if (typeof window === "undefined") {
    return false;
  }

  return window.sessionStorage.getItem(AUTH_STORAGE_KEY) === "true";
};

export const setAuthenticated = (): void => {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(AUTH_STORAGE_KEY, "true");
};

export const clearAuthenticated = (): void => {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
};

// Utility functions for data transformation
export const mapLogLevelToString = (level: number): string => {
  switch (level) {
    case 10:
      return "DEBUG";
    case 20:
      return "INFO";
    case 30:
      return "WARNING";
    case 40:
      return "ERROR";
    case 50:
      return "CRITICAL";
    default:
      return "UNKNOWN";
  }
};

export const formatTimestamp = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString();
};
