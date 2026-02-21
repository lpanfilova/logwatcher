// API client for LogWatcher backend integration
import axios from "axios";

const API_BASE_URL = "/api"; // Proxied to backend

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
