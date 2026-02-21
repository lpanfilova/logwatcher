import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Container,
  Row,
  Col,
  Button,
  Spinner,
  Alert,
  Card,
} from "react-bootstrap";
import {
  apiClient,
  type LogEntry,
  mapLogLevelToString,
  formatTimestamp,
} from "../api";

const LogDetails = () => {
  const { id } = useParams<{ id: string }>();
  const [log, setLog] = useState<LogEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const fetch = async () => {
      try {
        setLoading(true);
        setError(null);
        const entry = await apiClient.getLogById(id);
        setLog(entry);
      } catch (err) {
        console.error("Failed to fetch log:", err);
        setError("Failed to load log from server");
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, [id]);

  return (
    <Container fluid className="p-4">
      <div className="shadow rounded border bg-white mb-4 p-3 d-flex justify-content-between align-items-center">
        <h4 className="mb-0">Log Details</h4>
        <div>
          <Link to="/logs">
            <Button variant="outline-secondary">Back to Logs</Button>
          </Link>
        </div>
      </div>

      {loading && (
        <div className="text-center py-4">
          <Spinner animation="border" role="status" />
        </div>
      )}

      {error && <Alert variant="danger">{error}</Alert>}

      {!loading && log && (
        <Row>
          <Col md={8}>
            <Card className="shadow-sm">
              <Card.Body>
                <Card.Title>Message</Card.Title>
                <Card.Text className="text-break">
                  {log.msg || log.message}
                </Card.Text>

                <hr />

                <div className="mb-2">
                  <strong>ID:</strong> {log.id}
                </div>
                <div className="mb-2">
                  <strong>Time:</strong> {formatTimestamp(log.timestamp)}
                </div>
                <div className="mb-2">
                  <strong>Service:</strong> {log.service}
                </div>
                <div className="mb-2">
                  <strong>Source:</strong> {log.source}
                </div>
                <div className="mb-2">
                  <strong>Level:</strong> {mapLogLevelToString(log.level)}
                </div>
                {log.event && (
                  <div className="mb-2">
                    <strong>Event:</strong> {log.event}
                  </div>
                )}

                <hr />

                <Card.Subtitle className="mb-2 text-muted">
                  Raw message
                </Card.Subtitle>
                <pre style={{ whiteSpace: "pre-wrap" }}>{log.message}</pre>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </Container>
  );
};

export default LogDetails;
