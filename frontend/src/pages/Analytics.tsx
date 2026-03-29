import { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";
import { Col, Container, Form, Row, Spinner, Button } from "react-bootstrap";
import {
  apiClient,
  type ByEventData,
  type ErrorMetricsData,
  type LogVolumeData,
  type TopErrorsData,
} from "../api";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const CHART_COLORS = {
  primaryBg: "rgba(75, 126, 192, 0.7)",
  primaryBorder: "rgb(75, 126, 192)",
  dangerBg: "rgba(220, 53, 69, 0.65)",
  dangerBorder: "rgb(220, 53, 69)",
};

const Analytics = () => {
  const [interval, setInterval] = useState("1h");
  const [service, setService] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [byEvent, setByEvent] = useState<ByEventData>({ events: [] });
  const [logVolume, setLogVolume] = useState<LogVolumeData>({
    interval: "1h",
    data: [],
  });
  const [errorMetrics, setErrorMetrics] = useState<ErrorMetricsData>({
    interval: "1h",
    total_errors: 0,
    data: [],
  });
  const [topErrors, setTopErrors] = useState<TopErrorsData>({ top_errors: [] });

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);

      const serviceParam = service.trim() || undefined;

      const [
        byEventResponse,
        logVolumeResponse,
        errorsResponse,
        topErrorsResponse,
      ] = await Promise.all([
        apiClient.getMetricsByEvent(),
        apiClient.getLogVolumeMetrics(interval, serviceParam),
        apiClient.getErrorMetrics(interval, serviceParam),
        apiClient.getTopErrorsMetrics(10, serviceParam),
      ]);

      setByEvent(byEventResponse);
      setLogVolume(logVolumeResponse);
      setErrorMetrics(errorsResponse);
      setTopErrors(topErrorsResponse);
    } catch (err) {
      console.error("Failed to fetch analytics data:", err);
      setError("Failed to load analytics data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, [interval]);

  const formatTime = (timestamp: string) =>
    new Date(timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        ticks: { autoSkip: true, maxTicksLimit: 10 },
      },
      y: {
        beginAtZero: true,
        ticks: { precision: 0 },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  const logVolumeChartData = {
    labels: logVolume.data
      .slice(-20)
      .map((point) => formatTime(point.timestamp)),
    datasets: [
      {
        label: "Total Log Volume",
        data: logVolume.data.slice(-20).map((point) => point.total),
        backgroundColor: CHART_COLORS.primaryBg,
        borderColor: CHART_COLORS.primaryBorder,
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const errorTrendChartData = {
    labels: errorMetrics.data
      .slice(-20)
      .map((point) => formatTime(point.timestamp)),
    datasets: [
      {
        label: "Error Count",
        data: errorMetrics.data.slice(-20).map((point) => point.count),
        backgroundColor: CHART_COLORS.dangerBg,
        borderColor: CHART_COLORS.dangerBorder,
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const byEventChartData = {
    labels: byEvent.events.slice(0, 8).map((item) => item.event || "unknown"),
    datasets: [
      {
        label: "Events by Type",
        data: byEvent.events.slice(0, 8).map((item) => item.count),
        backgroundColor: CHART_COLORS.primaryBg,
        borderColor: CHART_COLORS.primaryBorder,
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  return (
    <Container fluid className="p-4" style={{ height: "calc(100vh - 40px)" }}>
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
              className="bi bi-bar-chart-line-fill me-3"
              style={{ fontSize: "2rem" }}
            ></i>
            <h2 className="fw-bold mb-0">Analytics Dashboard</h2>
          </div>
          <div className="text-center opacity-75">
            <small className="d-block">
              <i className="bi bi-exclamation-triangle me-1"></i>
              Total Errors: {errorMetrics.total_errors} |
              <i className="bi bi-diagram-3 ms-2 me-1"></i>
              Event Types: {byEvent.events.length}
            </small>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div
        className="shadow-lg border-0 mb-4 position-relative overflow-hidden"
        style={{
          borderRadius: "15px",
          background: "white",
          backdropFilter: "blur(10px)",
        }}
      >
        <div className="p-4">
          <div className="d-flex align-items-center mb-4">
            <i
              className="bi bi-sliders text-primary me-3"
              style={{ fontSize: "1.5rem" }}
            ></i>
            <h4 className="fw-bold mb-0 text-dark">Filters & Controls</h4>
          </div>

          <Row className="g-3">
            <Col md={3}>
              <Form.Select
                value={interval}
                onChange={(e) => setInterval(e.target.value)}
                className="border-0 shadow-sm"
                style={{
                  borderRadius: "10px",
                  background: "white",
                }}
              >
                <option value="1m">1 Minute</option>
                <option value="5m">5 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="1d">1 Day</option>
              </Form.Select>
            </Col>
            <Col md={5}>
              <Form.Control
                placeholder="Filter by service (optional)"
                value={service}
                onChange={(e) => setService(e.target.value)}
                className="border-0 shadow-sm"
                style={{
                  borderRadius: "10px",
                  background: "white",
                }}
              />
            </Col>
            <Col md={4}>
              <Button
                className="w-100 border-0 shadow-sm fw-semibold"
                style={{
                  borderRadius: "10px",
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  border: "none",
                }}
                onClick={fetchAnalyticsData}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Spinner size="sm" className="me-2" />
                    Loading...
                  </>
                ) : (
                  <>
                    <i className="bi bi-arrow-clockwise me-2"></i>
                    Refresh Data
                  </>
                )}
              </Button>
            </Col>
          </Row>
        </div>
      </div>

      {/* Error Alert */}
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
            <strong>Warning:</strong> {error}
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div
          className="shadow-lg border-0 position-relative overflow-hidden"
          style={{
            borderRadius: "15px",
            background: "white",
            backdropFilter: "blur(10px)",
            height: "60vh",
          }}
        >
          <div className="d-flex flex-column justify-content-center align-items-center h-100">
            <div
              className="spinner-border text-primary mb-3"
              role="status"
              style={{ width: "3rem", height: "3rem" }}
            >
              <span className="visually-hidden">Loading...</span>
            </div>
            <h5 className="text-muted mb-2">Loading Analytics</h5>
            <p className="text-muted small text-center">
              Fetching metrics and building charts...
              <br />
              This may take a moment for large datasets.
            </p>
          </div>
        </div>
      ) : (
        <div style={{ height: "calc(100% - 200px)" }}>
          {/* Top Row */}
          <Row className="g-4 mb-4 h-max">
            <Col md={6} className="h-max">
              <div
                className="shadow-lg border-0 h-100 position-relative overflow-hidden"
                style={{
                  borderRadius: "15px",
                  background: "white",
                  backdropFilter: "blur(10px)",
                }}
              >
                <div className="p-4 h-100 d-flex flex-column">
                  <div className="d-flex align-items-center mb-4">
                    <i
                      className="bi bi-bar-chart text-primary me-3"
                      style={{ fontSize: "1.5rem" }}
                    ></i>
                    <h4 className="fw-bold mb-0 text-dark">Log Volume</h4>
                  </div>
                  <div
                    className="grow position-relative"
                    style={{
                      background:
                        "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)",
                      borderRadius: "10px",
                      padding: "20px",
                    }}
                  >
                    <Bar data={logVolumeChartData} options={chartOptions} />
                  </div>
                </div>
              </div>
            </Col>

            <Col md={6} className="h-max">
              <div
                className="shadow-lg border-0 h-100 position-relative overflow-hidden"
                style={{
                  borderRadius: "15px",
                  background: "white",
                  backdropFilter: "blur(10px)",
                }}
              >
                <div className="p-4 h-100 d-flex flex-column">
                  <div className="d-flex align-items-center mb-4">
                    <i
                      className="bi bi-exclamation-triangle-fill text-danger me-3"
                      style={{ fontSize: "1.5rem" }}
                    ></i>
                    <h4 className="fw-bold mb-0 text-dark">Top Errors</h4>
                  </div>
                  <div className="grow">
                    {topErrors.top_errors.length === 0 ? (
                      <div className="d-flex align-items-center justify-content-center h-100">
                        <div className="text-center text-muted">
                          <i
                            className="bi bi-check-circle"
                            style={{ fontSize: "3rem" }}
                          ></i>
                          <div className="mt-3">No errors found!</div>
                          <small>All systems running smoothly</small>
                        </div>
                      </div>
                    ) : (
                      <div
                        style={{
                          maxHeight: "100%",
                          overflow: "auto",
                          background:
                            "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)",
                          borderRadius: "10px",
                          padding: "15px",
                        }}
                      >
                        {topErrors.top_errors
                          .slice(0, 7)
                          .map((item, _index) => (
                            <div
                              className="border-0 rounded mb-3 shadow-sm"
                              key={`${item.event}-${item.count}`}
                              style={{
                                background: "white",
                                borderRadius: "8px",
                                padding: "12px",
                              }}
                            >
                              <div className="d-flex justify-content-between align-items-start">
                                <div className="grow me-3">
                                  <strong className="text-dark">
                                    {item.event || "unknown"}
                                  </strong>
                                  <div className="text-muted small mt-1">
                                    Error event
                                  </div>
                                </div>
                                <div className="text-end">
                                  <span
                                    className="badge bg-danger text-white px-3 py-2"
                                    style={{ borderRadius: "20px" }}
                                  >
                                    {item.count}
                                  </span>
                                  <div className="text-muted small mt-1">
                                    occurrences
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Col>
          </Row>

          {/* Bottom Row */}
          <Row className="g-4 h-50">
            <Col md={6} className="h-max">
              <div
                className="shadow-lg border-0 h-100 position-relative overflow-hidden"
                style={{
                  borderRadius: "15px",
                  background: "white",
                  backdropFilter: "blur(10px)",
                }}
              >
                <div className="p-4 h-100 d-flex flex-column">
                  <div className="d-flex align-items-center mb-4">
                    <i
                      className="bi bi-graph-up-arrow text-warning me-3"
                      style={{ fontSize: "1.5rem" }}
                    ></i>
                    <h4 className="fw-bold mb-0 text-dark">Error Trends</h4>
                  </div>
                  <div
                    className="grow position-relative"
                    style={{
                      background:
                        "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)",
                      borderRadius: "10px",
                      padding: "20px",
                    }}
                  >
                    <Bar data={errorTrendChartData} options={chartOptions} />
                  </div>
                </div>
              </div>
            </Col>

            <Col md={6} className="h-max">
              <div
                className="shadow-lg border-0 h-100 position-relative overflow-hidden"
                style={{
                  borderRadius: "15px",
                  background: "white",
                  backdropFilter: "blur(10px)",
                }}
              >
                <div className="p-4 h-100 d-flex flex-column">
                  <div className="d-flex align-items-center mb-4">
                    <i
                      className="bi bi-pie-chart-fill text-info me-3"
                      style={{ fontSize: "1.5rem" }}
                    ></i>
                    <h4 className="fw-bold mb-0 text-dark">Events by Type</h4>
                  </div>
                  <div
                    className="grow position-relative mb-3"
                    style={{
                      background:
                        "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)",
                      borderRadius: "10px",
                      padding: "20px",
                    }}
                  >
                    <Bar data={byEventChartData} options={chartOptions} />
                  </div>
                  <div className="text-center">
                    <small className="text-muted">
                      <i className="bi bi-info-circle me-1"></i>
                      Top events:{" "}
                      {byEvent.events
                        .slice(0, 4)
                        .map((e) => e.event || "unknown")
                        .join(", ") || "none"}
                    </small>
                  </div>
                </div>
              </div>
            </Col>
          </Row>
        </div>
      )}
    </Container>
  );
};

export default Analytics;
