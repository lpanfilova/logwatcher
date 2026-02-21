// Mock data for dashboard - can be replaced with backend integration
export interface LogEntry {
  time: string;
  service: string;
  level: string;
  message: string;
}

export interface ChartDataResponse {
  labels: string[];
  value: number[];
}

// Mock logs data
export const getMockLogs = (): LogEntry[] => {
  return [
    {
      time: "2025-02-11 14:32:15",
      service: "auth-service",
      level: "ERROR",
      message: "Failed login attempt from IP 192.168.1.100",
    },
    {
      time: "2025-02-11 14:28:42",
      service: "api-gateway",
      level: "WARNING",
      message: "Slow response detected - 5.2 seconds",
    },
    {
      time: "2025-02-11 14:15:03",
      service: "database",
      level: "ERROR",
      message: "Database connection failed",
    },
    {
      time: "2025-02-11 14:05:28",
      service: "payment-service",
      level: "INFO",
      message: "Payment processed successfully",
    },
    {
      time: "2025-02-11 13:55:12",
      service: "cache-service",
      level: "WARNING",
      message: "High memory usage - 89%",
    },
    {
      time: "2025-02-11 13:42:19",
      service: "email-service",
      level: "ERROR",
      message: "Failed to send email notification",
    },
    {
      time: "2025-02-11 13:30:05",
      service: "auth-service",
      level: "INFO",
      message: "User session created",
    },
    {
      time: "2025-02-11 13:15:44",
      service: "api-gateway",
      level: "ERROR",
      message: "Request timeout after 30 seconds",
    },
  ];
};

// Mock error trend data
export const getMockErrorTrend = (): ChartDataResponse => {
  return {
    labels: ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "23:59"],
    value: [12, 19, 8, 15, 22, 18, 24],
  };
};

// Helper function to count incidents from logs
export const countIncidents = (logs: LogEntry[]): Record<string, number> => {
  return logs.reduce(
    (acc, log) => {
      acc[log.message] = (acc[log.message] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );
};
