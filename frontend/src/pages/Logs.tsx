import { useState, useEffect } from "react";
import {
  Container,
  Table,
  Row,
  Col,
  Form,
  InputGroup,
  Spinner,
  Button,
} from "react-bootstrap";
import { Link } from "react-router-dom";
import { BsSearch } from "react-icons/bs";
import {
  apiClient,
  type LogEntry,
  type LogsResponse,
  mapLogLevelToString,
  formatTimestamp,
} from "../api";

const Logs = () => {
  // State management
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalLogs, setTotalLogs] = useState(0);

  // Filters state
  const [searchQuery, setSearchQuery] = useState("");
  const [serviceFilter, setServiceFilter] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [minLevelFilter, setMinLevelFilter] = useState("");

  // Fetch logs function
  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        size: 100, // Get up to 100 logs
      };

      if (searchQuery.trim()) {
        params.q = searchQuery.trim();
      }

      if (serviceFilter.trim()) {
        params.service = serviceFilter.trim();
      }

      if (levelFilter) {
        params.level = parseInt(levelFilter);
      }

      if (minLevelFilter) {
        params.min_level = parseInt(minLevelFilter);
      }

      const response: LogsResponse = await apiClient.getLogs(params);
      setLogs(response.logs);
      setTotalLogs(response.total);
    } catch (err) {
      console.error("Failed to fetch logs:", err);
      setError("Failed to load logs from server");
      // Could set mock data here as fallback, but for now just show error
    } finally {
      setLoading(false);
    }
  };

  // Fetch logs on component mount and when filters change
  useEffect(() => {
    fetchLogs();
  }, [searchQuery, serviceFilter, levelFilter, minLevelFilter]);

  const levelOptions = [
    { value: "", label: "All Levels" },
    { value: "50", label: "ERROR" },
    { value: "40", label: "WARNING" },
    { value: "30", label: "INFO" },
    { value: "20", label: "DEBUG" },
  ];

  const minLevelOptions = [
    { value: "", label: "No Min Level" },
    { value: "50", label: "ERROR+" },
    { value: "40", label: "WARNING+" },
    { value: "30", label: "INFO+" },
    { value: "20", label: "DEBUG+" },
  ];

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
              className="bi bi-journal-text me-3"
              style={{ fontSize: "2rem" }}
            ></i>
            <h2 className="fw-bold mb-0">System Logs</h2>
          </div>
          {totalLogs > 0 && (
            <div className="text-center opacity-75">
              <small className="d-block">
                <i className="bi bi-bar-chart-line me-1"></i>
                Total: {totalLogs} logs
              </small>
            </div>
          )}
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
              className="bi bi-funnel-fill text-primary me-3"
              style={{ fontSize: "1.5rem" }}
            ></i>
            <h4 className="fw-bold mb-0 text-dark">Filters & Search</h4>
          </div>

          <Row className="g-3">
            <Col md={4}>
              <InputGroup>
                <InputGroup.Text
                  className="border-0"
                  style={{
                    background:
                      "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)",
                    borderRadius: "10px 0 0 10px",
                  }}
                >
                  <BsSearch className="text-primary" />
                </InputGroup.Text>
                <Form.Control
                  placeholder="Search logs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="border-0 shadow-sm"
                  style={{
                    borderRadius: "0 10px 10px 0",
                    background: "white",
                  }}
                />
              </InputGroup>
            </Col>
            <Col md={2}>
              <Form.Control
                placeholder="Filter service"
                value={serviceFilter}
                onChange={(e) => setServiceFilter(e.target.value)}
                className="border-0 shadow-sm"
                style={{
                  borderRadius: "10px",
                  background: "white",
                }}
              />
            </Col>
            <Col md={2}>
              <Form.Select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                className="border-0 shadow-sm"
                style={{
                  borderRadius: "10px",
                  background: "white",
                }}
              >
                {levelOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Form.Select>
            </Col>
            <Col md={2}>
              <Form.Select
                value={minLevelFilter}
                onChange={(e) => setMinLevelFilter(e.target.value)}
                className="border-0 shadow-sm"
                style={{
                  borderRadius: "10px",
                  background: "white",
                }}
              >
                {minLevelOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Form.Select>
            </Col>
            <Col md={2}>
              <Button
                className="w-100 border-0 shadow-sm fw-semibold"
                style={{
                  borderRadius: "10px",
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  border: "none",
                }}
                onClick={fetchLogs}
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
                    Refresh
                  </>
                )}
              </Button>
            </Col>
          </Row>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div
          className="alert border-0 shadow-sm mb-4 d-flex align-items-center"
          style={{
            borderRadius: "10px",
            background: "linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%)",
            border: "1px solid #dc3545",
          }}
        >
          <i
            className="bi bi-exclamation-triangle-fill text-danger me-3"
            style={{ fontSize: "1.2rem" }}
          ></i>
          <div>
            <strong>Error:</strong> {error}
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div
          className="shadow-lg border-0 mb-4 position-relative overflow-hidden"
          style={{
            borderRadius: "15px",
            background: "white",
            backdropFilter: "blur(10px)",
          }}
        >
          <div className="p-5 text-center">
            <div
              className="spinner-border text-primary mb-3"
              role="status"
              style={{ width: "3rem", height: "3rem" }}
            >
              <span className="visually-hidden">Loading...</span>
            </div>
            <h5 className="text-muted mb-2">Fetching Logs</h5>
            <p className="text-muted small">
              Please wait while we load your system logs...
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && logs.length === 0 && (
        <div
          className="shadow-lg border-0 mb-4 position-relative overflow-hidden"
          style={{
            borderRadius: "15px",
            background: "white",
            backdropFilter: "blur(10px)",
          }}
        >
          <div className="p-5 text-center">
            <i
              className="bi bi-journal-x text-muted"
              style={{ fontSize: "4rem" }}
            ></i>
            <h5 className="text-muted mt-3 mb-2">No Logs Available</h5>
            <p className="text-muted">
              Waiting for log data to be collected...
            </p>
          </div>
        </div>
      )}

      {/* Logs Table */}
      {!loading && logs.length > 0 && (
        <div
          className="shadow-lg border-0 position-relative overflow-hidden"
          style={{
            borderRadius: "15px",
            background: "white",
            backdropFilter: "blur(10px)",
          }}
        >
          <div className="p-4">
            <div className="d-flex align-items-center justify-content-between mb-4">
              <div className="d-flex align-items-center">
                <i
                  className="bi bi-table text-primary me-3"
                  style={{ fontSize: "1.5rem" }}
                ></i>
                <h4 className="fw-bold mb-0 text-dark">Log Entries</h4>
              </div>
              <div className="text-muted small">
                Showing {logs.length} of {totalLogs} logs
              </div>
            </div>

            <div className="table-responsive">
              <Table hover className="mb-0">
                <thead
                  style={{
                    background:
                      "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    color: "white",
                  }}
                >
                  <tr>
                    <th className="fw-semibold border-0">
                      <i className="bi bi-hash me-2"></i>ID
                    </th>
                    <th className="fw-semibold border-0">
                      <i className="bi bi-calendar-event me-2"></i>Time
                    </th>
                    <th className="fw-semibold border-0">
                      <i className="bi bi-server me-2"></i>Service
                    </th>
                    <th className="fw-semibold border-0">
                      <i className="bi bi-exclamation-triangle me-2"></i>Level
                    </th>
                    <th className="fw-semibold border-0">
                      <i className="bi bi-chat-text me-2"></i>Message
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className="border-bottom border-light">
                      <td>
                        <Link
                          to={`/logs/${log.id}`}
                          className="text-decoration-none fw-semibold text-primary"
                          style={{ fontSize: "0.9rem" }}
                        >
                          {log.id.slice(0, 8)}...
                        </Link>
                      </td>
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
                        className="text-start text-truncate"
                        style={{ maxWidth: "400px" }}
                      >
                        {log.msg || log.message}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          </div>
        </div>
      )}
    </Container>
  );
};

export default Logs;
