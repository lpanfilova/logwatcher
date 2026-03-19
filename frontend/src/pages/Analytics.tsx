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
import { Alert, Col, Container, Form, Row, Spinner, Button } from "react-bootstrap";
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
  const [logVolume, setLogVolume] = useState<LogVolumeData>({ interval: "1h", data: [] });
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

      const [byEventResponse, logVolumeResponse, errorsResponse, topErrorsResponse] =
        await Promise.all([
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
    new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

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
    labels: logVolume.data.slice(-20).map((point) => formatTime(point.timestamp)),
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
    labels: errorMetrics.data.slice(-20).map((point) => formatTime(point.timestamp)),
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
    <Container fluid className="p-3" style={{ height: "calc(100vh - 40px)" }}>
      <div className="shadow rounded border bg-white mb-3">
        <h3 className="text-center p-2 mb-0">
          Analytics
          <small className="text-muted d-block">
            Total Errors: {errorMetrics.total_errors} | Event Types: {byEvent.events.length}
          </small>
        </h3>
      </div>

      <Row className="g-2 shadow rounded border bg-white p-2 mb-3">
        <Col md={3}>
          <Form.Select value={interval} onChange={(e) => setInterval(e.target.value)}>
            <option value="1m">1 Minute</option>
            <option value="5m">5 Minutes</option>
            <option value="1h">1 Hour</option>
            <option value="1d">1 Day</option>
          </Form.Select>
        </Col>
        <Col md={5}>
          <Form.Control
            placeholder="Filter service (optional)"
            value={service}
            onChange={(e) => setService(e.target.value)}
          />
        </Col>
        <Col md={2}>
          <Button variant="outline-primary" onClick={fetchAnalyticsData} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </Button>
        </Col>
      </Row>

      {error && (
        <Alert variant="warning" className="mb-3 py-2">
          {error}
        </Alert>
      )}

      {loading ? (
        <div className="shadow rounded border bg-white h-75 d-flex flex-column justify-content-center align-items-center">
          <Spinner animation="border" role="status" className="mb-2" />
          <p className="text-muted mb-0">Loading analytics...</p>
        </div>
      ) : (
        <div style={{ height: "calc(100% - 145px)" }}>
          <Row className="g-3 h-50 mb-1">
            <Col md={6} className="h-100">
              <div className="shadow rounded border bg-white p-3 h-100 d-flex flex-column">
                <h5 className="mb-2">Log Volume</h5>
                <div className="border rounded p-2 flex-grow-1">
                  <Bar data={logVolumeChartData} options={chartOptions} />
                </div>
              </div>
            </Col>

            <Col md={6} className="h-100">
              <div className="shadow rounded border bg-white p-3 h-100">
                <h5 className="mb-2">Top Errors</h5>
                {topErrors.top_errors.length === 0 ? (
                  <div className="text-muted">No error data available.</div>
                ) : (
                  topErrors.top_errors.slice(0, 7).map((item) => (
                    <div className="border rounded p-2 mb-2" key={`${item.event}-${item.count}`}>
                      <strong>{item.event || "unknown"}</strong>
                      <div className="text-muted">Occurrences: {item.count}</div>
                    </div>
                  ))
                )}
              </div>
            </Col>
          </Row>

          <Row className="g-3 h-50 mt-1">
            <Col md={6} className="h-100">
              <div className="shadow rounded border bg-white p-3 h-100 d-flex flex-column">
                <h5 className="mb-2">Errors Over Time</h5>
                <div className="border rounded p-2 flex-grow-1">
                  <Bar data={errorTrendChartData} options={chartOptions} />
                </div>
              </div>
            </Col>

            <Col md={6} className="h-100">
              <div className="shadow rounded border bg-white p-3 h-100 d-flex flex-column">
                <h5 className="mb-2">Events by Type</h5>
                <div className="border rounded p-2 flex-grow-1 mb-2">
                  <Bar data={byEventChartData} options={chartOptions} />
                </div>
                <small className="text-muted">
                  Top events: {byEvent.events.slice(0, 4).map((e) => e.event || "unknown").join(", ") || "none"}
                </small>
              </div>
            </Col>
          </Row>
        </div>
      )}
    </Container>
  );
};

export default Analytics;
