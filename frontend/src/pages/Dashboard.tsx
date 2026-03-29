import { Col, Container, Row, Table } from "react-bootstrap";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";
import { useEffect, useState } from "react";
import {
  apiClient,
  type LogEntry,
  type SummaryData,
  mapLogLevelToString,
  formatTimestamp,
} from "../api";
import { getMockLogs, getMockErrorTrend, countIncidents } from "../mockData.ts";
ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const Dashboard = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [chartData, setChartData] = useState({
    labels: [] as string[],
    datasets: [
      {
        label: "Log Events",
        data: [] as number[],
        backgroundColor: "rgba(75, 126, 192, 0.7)",
        borderColor: "rgb(75, 126, 192)",
        borderWidth: 1,
        borderRadius: 4,
        barPercentage: 0.9,
        categoryPercentage: 0.9,
      },
    ],
  });

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch summary data
        const summaryResponse = await apiClient.getSummary();
        setSummary(summaryResponse);

        // Fetch timeline data with finer granularity for minute-level visibility
        const timelineResponse = await apiClient.getTimelineMetrics("1m");

        // Only display the most recent 30 minutes of timeline points
        const halfHourAgo = Date.now() - 30 * 60 * 1000;
        const filteredPoints = timelineResponse.data.filter((point) => {
          const timestamp = new Date(point.timestamp).getTime();
          return timestamp >= halfHourAgo;
        });

        setChartData({
          labels: filteredPoints.map((point) => {
            const date = new Date(point.timestamp);
            return date.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            });
          }),
          datasets: [
            {
              label: "Log Events",
              data: filteredPoints.map((point) => point.count),
              backgroundColor: "rgba(75, 126, 192, 0.7)",
              borderColor: "rgb(75, 126, 192)",
              borderWidth: 1,
              borderRadius: 4,
              barPercentage: 0.9,
              categoryPercentage: 0.9,
            },
          ],
        });

        // Fetch recent logs
        const logsResponse = await apiClient.getLogs({
          size: 10,
          min_level: 30,
        }); // Get recent logs with warnings/errors
        setLogs(logsResponse.logs);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
        setError("Failed to load dashboard data");

        // Fallback to mock data
        const mockLogs = getMockLogs();
        const mockTrend = getMockErrorTrend();
        setLogs(
          mockLogs.map((log) => ({
            id: Math.random().toString(),
            timestamp: log.time,
            message: log.message,
            service: log.service,
            source: "stdout",
            level:
              log.level === "ERROR" ? 50 : log.level === "WARNING" ? 40 : 30,
            msg: log.message,
          })),
        );
        setChartData({
          labels: mockTrend.labels,
          datasets: [
            {
              label: "Log Events",
              data: mockTrend.value,
              backgroundColor: "rgba(75, 126, 192, 0.7)",
              borderColor: "rgb(75, 126, 192)",
              borderWidth: 1,
              borderRadius: 4,
              barPercentage: 0.9,
              categoryPercentage: 0.9,
            },
          ],
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Count occurrences of each incident message dynamically
  const incidentCounts = countIncidents(
    logs.map((log) => ({
      time: formatTimestamp(log.timestamp),
      service: log.service,
      level: mapLogLevelToString(log.level),
      message: log.msg || log.message,
    })),
  );

  const recurringMessages = Object.entries(incidentCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  const truncateLabel = (value: string, max: number = 40) =>
    value.length > max ? `${value.slice(0, max)}...` : value;

  const recurringMessagesChartData = {
    labels: recurringMessages.map(([message]) => truncateLabel(message)),
    datasets: [
      {
        label: "Occurrences",
        data: recurringMessages.map(([, count]) => count),
        backgroundColor: "rgba(255, 193, 7)",
        borderColor: "rgb(255, 193, 7)",
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  //Chart data
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        ticks: {
          autoSkip: true,
          maxTicksLimit: 16,
        },
      },
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
          stepSize: 5,
        },
        max: 50,
      },
    },
  };

  const recurringChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: "y" as const,
    scales: {
      x: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
      y: {
        ticks: {
          autoSkip: false,
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  return (
    <Container fluid className="p-4">
      {/* Header */}
      <div
        className="shadow-lg border-0 mb-4 position-relative overflow-hidden"
        style={{
          borderRadius: "15px",
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          color: "white",
        }}
      >
        <div className="p-4">
          <div className="d-flex align-items-center justify-content-center mb-2">
            <i
              className="bi bi-speedometer2 me-3"
              style={{ fontSize: "2rem" }}
            ></i>
            <h2 className="fw-bold mb-0">Dashboard</h2>
          </div>
          {summary && (
            <div className="text-center opacity-75">
              <small className="d-block">
                <i className="bi bi-bar-chart-line me-1"></i>
                Total Logs: {summary.total_logs} |
                <i className="bi bi-server ms-2 me-1"></i>
                Services: {summary.services.length}
              </small>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div
          className="alert border-0 shadow-sm mb-4 d-flex align-items-center"
          style={{
            borderRadius: "10px",
            background: "linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%)",
            border: "1px solid #ffc107",
          }}
        >
          <i
            className="bi bi-exclamation-triangle-fill text-warning me-3"
            style={{ fontSize: "1.2rem" }}
          ></i>
          <div>
            <strong>Warning:</strong> {error} - Showing mock data as fallback.
          </div>
        </div>
      )}

      {/* Top Section */}
      <Row className="g-4 mb-4">
        <Col md={7}>
          <div
            className="shadow-lg border-0 h-100 position-relative overflow-hidden"
            style={{
              borderRadius: "15px",
              background: "white",
              backdropFilter: "blur(10px)",
            }}
          >
            <div className="p-4">
              <div className="d-flex align-items-center mb-4">
                <i
                  className="bi bi-clock-history text-primary me-3"
                  style={{ fontSize: "1.5rem" }}
                ></i>
                <h4 className="fw-bold mb-0 text-dark">Recent Logs</h4>
              </div>
              {loading ? (
                <div className="text-center py-5">
                  <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  <div className="mt-3 text-muted">Loading logs...</div>
                </div>
              ) : (
                <div className="table-responsive">
                  <Table hover className="mb-0">
                    <thead
                      style={{
                        background:
                          "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)",
                      }}
                    >
                      <tr>
                        <th className="fw-semibold text-dark border-0">
                          <i className="bi bi-calendar-event me-2"></i>Time
                        </th>
                        <th className="fw-semibold text-dark border-0">
                          <i className="bi bi-server me-2"></i>Service
                        </th>
                        <th className="fw-semibold text-dark border-0">
                          <i className="bi bi-exclamation-triangle me-2"></i>
                          Level
                        </th>
                        <th className="fw-semibold text-dark border-0">
                          <i className="bi bi-chat-text me-2"></i>Message
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.slice(0, 6).map((log) => (
                        <tr key={log.id} className="border-bottom border-light">
                          <td className="text-muted small">
                            {formatTimestamp(log.timestamp)}
                          </td>
                          <td className="fw-medium">{log.service}</td>
                          <td>
                            <span
                              className={`badge border-0 px-3 py-2 ${
                                log.level >= 50
                                  ? "bg-danger"
                                  : log.level >= 40
                                    ? "bg-warning text-dark"
                                    : log.level >= 30
                                      ? "bg-info"
                                      : "bg-secondary"
                              }`}
                              style={{
                                borderRadius: "20px",
                                fontSize: "0.75rem",
                              }}
                            >
                              {mapLogLevelToString(log.level)}
                            </span>
                          </td>
                          <td
                            className="text-truncate"
                            style={{ maxWidth: "300px" }}
                          >
                            {log.msg || log.message}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </div>
              )}
            </div>
          </div>
        </Col>

        <Col md={5}>
          <div
            className="shadow-lg border-0 position-relative overflow-hidden"
            style={{
              borderRadius: "15px",
              background: "white",
              backdropFilter: "blur(10px)",
            }}
          >
            <div className="p-4">
              <div className="d-flex align-items-center mb-4">
                <i
                  className="bi bi-arrow-repeat text-primary me-3"
                  style={{ fontSize: "1.5rem" }}
                ></i>
                <h4 className="fw-bold mb-0 text-dark">Recurring Messages</h4>
              </div>
              <div
                className="border-0 rounded mb-3 position-relative"
                style={{
                  height: "220px",
                  background:
                    "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)",
                  borderRadius: "10px",
                }}
              >
                {loading ? (
                  <div className="d-flex align-items-center justify-content-center h-100">
                    <div className="text-center">
                      <div
                        className="spinner-border text-primary mb-2"
                        role="status"
                      ></div>
                      <div className="text-muted small">Loading chart...</div>
                    </div>
                  </div>
                ) : recurringMessages.length === 0 ? (
                  <div className="d-flex align-items-center justify-content-center h-100">
                    <div className="text-center text-muted">
                      <i
                        className="bi bi-bar-chart-line"
                        style={{ fontSize: "2rem" }}
                      ></i>
                      <div className="mt-2 small">
                        No recurring messages found
                      </div>
                    </div>
                  </div>
                ) : (
                  <Bar
                    data={recurringMessagesChartData}
                    options={recurringChartOptions}
                  />
                )}
              </div>
              <div
                style={{
                  maxHeight: "110px",
                  overflow: "auto",
                  overflowX: "hidden",
                  background:
                    "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)",
                  borderRadius: "10px",
                  padding: "10px",
                }}
              >
                {recurringMessages.map(([message, count]) => (
                  <div
                    className="border-0 rounded p-3 mb-2 shadow-sm"
                    key={message}
                    style={{
                      background: "white",
                      borderRadius: "8px",
                    }}
                  >
                    <div className="d-flex justify-content-between align-items-start">
                      <strong className="text-dark small grow me-2">
                        {truncateLabel(message, 70)}
                      </strong>
                      <span
                        className="badge bg-primary text-white px-2 py-1 small"
                        style={{ borderRadius: "12px" }}
                      >
                        {count}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Col>
      </Row>

      {/* Bottom Section */}
      <Row className="g-4">
        <Col>
          <div
            className="shadow-lg border-0 position-relative overflow-hidden"
            style={{
              borderRadius: "15px",
              background: "white",
              backdropFilter: "blur(10px)",
            }}
          >
            <div className="p-4">
              <div className="d-flex align-items-center mb-4">
                <i
                  className="bi bi-graph-up text-primary me-3"
                  style={{ fontSize: "1.5rem" }}
                ></i>
                <h3 className="fw-bold mb-0 text-dark">Log Events Timeline</h3>
              </div>
              <div
                className="border-0 rounded position-relative"
                style={{
                  height: "400px",
                  background:
                    "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)",
                  borderRadius: "10px",
                }}
              >
                {loading ? (
                  <div className="d-flex align-items-center justify-content-center h-100">
                    <div className="text-center">
                      <div
                        className="spinner-border text-primary mb-2"
                        role="status"
                      ></div>
                      <div className="text-muted">Loading timeline data...</div>
                    </div>
                  </div>
                ) : (
                  <Bar data={chartData} options={chartOptions} />
                )}
              </div>
            </div>
          </div>
        </Col>
      </Row>
    </Container>
  );
};

export default Dashboard;
