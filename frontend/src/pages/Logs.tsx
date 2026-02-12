import { useState, useEffect } from "react";
import { Container, Table, Row, Col, Form, InputGroup, Spinner, Alert } from "react-bootstrap";
import { BsSearch } from "react-icons/bs";

interface LogEntry {
  id: string | number;
  time: string | number;
  service: string;
  level: string;
  message: string;
}

const Logs = () => {
  // Mock logs data
  const mockLogs: LogEntry[] = [
    { id: 1, time: "12:30", service: "Auth-service", level: "error", message: "Something went wrong" },
    { id: 2, time: "14:30", service: "Payment-service", level: "info", message: "Payment processed" },
    { id: 3, time: "16:00", service: "Auth-service", level: "warn", message: "Password attempt failed" },
    { id: 4, time: "18:00", service: "Notification-service", level: "info", message: "Email sent" },
  ];

  // State management
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch logs on component mount with sequence of states
  useEffect(() => {
    // Step 1: Show error state (2 seconds)
    setError("Failed to load logs. Please try again.");
    setLogs([]);
    setLoading(false);

    const timer1 = setTimeout(() => {
      // Step 2: Show empty state (2 seconds)
      setError(null);
      setLogs([]);
      setLoading(false);
    }, 2000);

    const timer2 = setTimeout(() => {
      // Step 3: Show loading state (3 seconds)
      setError(null);
      setLogs([]);
      setLoading(true);
    }, 4000);

    const timer3 = setTimeout(() => {
      // Step 4: Show data
      setLogs(mockLogs);
      setLoading(false);
    }, 7000);

    // Cleanup timers on unmount
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, []);

  // Filters state
  const [idFilter, setIdFilter] = useState("");
  const [timeFilter, setTimeFilter] = useState("");
  const [serviceFilter, setServiceFilter] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [messageFilter, setMessageFilter] = useState("");

  // Filter logs
  const filteredLogs = logs.filter(
    (log) =>
      (idFilter === "" || log.id.toString().includes(idFilter)) &&
      (timeFilter === "" || log.time.toString().includes(timeFilter)) &&
      (serviceFilter === "" || log.service.toLowerCase().includes(serviceFilter.toLowerCase())) &&
      (levelFilter === "" || log.level === levelFilter) &&
      (messageFilter === "" || log.message.toLowerCase().includes(messageFilter.toLowerCase()))
  );

  // Function to assign bootstrap text color based on level
  const levelColor = (level: string) => {
    switch (level) {
      case "error":
        return "text-danger";
      case "warn":
        return "text-warning";
      case "info":
        return "text-success";
      default:
        return "";
    }
  };

  return (
    <Container fluid className="p-4">
      {/* Shadowed, bordered card-style container */}
      <div className=" shadow rounded border bg-white mb-4">
        {/* Title */}
        <h3 className="text-center p-2 ">System Logs</h3>
      </div>
      {/* Filters */}
      <Row className="mb-3 g-2 shadow rounded border bg-white p-3">
        <Col md={2}>
          <InputGroup>
            <InputGroup.Text>
              <BsSearch />
            </InputGroup.Text>
            <Form.Control placeholder="Filter ID" value={idFilter} onChange={(e) => setIdFilter(e.target.value)} />
          </InputGroup>
        </Col>
        <Col md={2}>
          <InputGroup>
            <InputGroup.Text>
              <BsSearch />
            </InputGroup.Text>
            <Form.Control placeholder="Filter Time" value={timeFilter} onChange={(e) => setTimeFilter(e.target.value)} />
          </InputGroup>
        </Col>
        <Col md={3}>
          <InputGroup>
            <InputGroup.Text>
              <BsSearch />
            </InputGroup.Text>
            <Form.Control placeholder="Filter Service" value={serviceFilter} onChange={(e) => setServiceFilter(e.target.value)} />
          </InputGroup>
        </Col>
        <Col md={2}>
          <Form.Select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)}>
            <option value="">Filter Level</option>
            <option value="error">Error</option>
            <option value="warn">Warn</option>
            <option value="info">Info</option>
          </Form.Select>
        </Col>
        <Col md={3}>
          <InputGroup>
            <InputGroup.Text>
              <BsSearch />
            </InputGroup.Text>
            <Form.Control placeholder="Filter Message" value={messageFilter} onChange={(e) => setMessageFilter(e.target.value)} />
          </InputGroup>
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
      {!loading && (
        <Row className="shadow rounded border bg-white p-3">
          <Table striped bordered hover responsive className="shadow-sm align-middle rounded border  text-center">
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
              {filteredLogs.length > 0 ? (
                filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td>{log.id}</td>
                    <td>{log.time}</td>
                    <td>{log.service}</td>
                    <td className={levelColor(log.level)}>{log.level.toUpperCase()}</td>
                    <td>{log.message}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="text-center text-muted py-3">
                    No logs found matching your filters
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        </Row>
      )}
    </Container>
  );
};

export default Logs;
