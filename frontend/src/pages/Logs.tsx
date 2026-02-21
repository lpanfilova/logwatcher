import { useState, useEffect } from "react";
import {
  Container,
  Table,
  Row,
  Col,
  Form,
  InputGroup,
  Spinner,
  Alert,
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

      if (serviceFilter) {
        params.service = serviceFilter;
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

  // Function to assign bootstrap text color based on level
  const levelColor = (level: number) => {
    if (level >= 50) return "text-danger"; // ERROR, CRITICAL
    if (level >= 40) return "text-warning"; // WARNING
    if (level >= 30) return "text-info"; // INFO
    return "text-secondary"; // DEBUG
  };

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
      {/* Shadowed, bordered card-style container */}
      <div className=" shadow rounded border bg-white mb-4">
        {/* Title */}
        <h3 className="text-center p-2">
          System Logs
          {totalLogs > 0 && (
            <small className="text-muted d-block">
              Total: {totalLogs} logs
            </small>
          )}
        </h3>
      </div>

      {/* Filters */}
      <Row className="mb-3 g-2 shadow rounded border bg-white p-3">
        <Col md={4}>
          <InputGroup>
            <InputGroup.Text>
              <BsSearch />
            </InputGroup.Text>
            <Form.Control
              placeholder="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </InputGroup>
        </Col>
        <Col md={2}>
          <Form.Control
            placeholder="Filter Service"
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
          />
        </Col>
        <Col md={2}>
          <Form.Select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
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
            variant="outline-primary"
            onClick={fetchLogs}
            disabled={loading}
          >
            {loading ? "Loading..." : "Refresh"}
          </Button>
        </Col>
      </Row>

      {/* Error State */}
      {error && (
        <Row className="mb-3">
          <Col>
            <Alert variant="danger" dismissible onClose={() => setError(null)}>
              {error}
            </Alert>
          </Col>
        </Row>
      )}

      {/* Loading State */}
      {loading && (
        <Row className="shadow rounded border bg-white p-5 text-center mb-4">
          <Col>
            <Spinner animation="border" role="status" className="mb-2">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
            <p className="text-muted mt-2">Fetching logs...</p>
          </Col>
        </Row>
      )}

      {/* Empty State */}
      {!loading && !error && logs.length === 0 && (
        <Row className="shadow rounded border bg-white p-5 text-center mb-4">
          <Col>
            <p className="text-muted">No logs available. Waiting for data...</p>
          </Col>
        </Row>
      )}

      {/* Styled Table */}
      {!loading && logs.length > 0 && (
        <Row className="shadow rounded border bg-white p-3">
          <Table
            striped
            bordered
            hover
            responsive
            className="shadow-sm align-middle rounded border text-center"
          >
            <thead className="table-dark rounded border text-center">
              <tr>
                <th>ID</th>
                <th>Time</th>
                <th>Service</th>
                <th>Level</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>
                    <Link to={`/logs/${log.id}`}>{log.id}</Link>
                  </td>
                  <td>{formatTimestamp(log.timestamp)}</td>
                  <td>{log.service}</td>
                  <td className={levelColor(log.level)}>
                    {mapLogLevelToString(log.level)}
                  </td>
                  <td className="text-start">{log.msg || log.message}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Row>
      )}
    </Container>
  );
};

export default Logs;
