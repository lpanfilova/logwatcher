import { useState, type FormEvent } from "react";
import { Alert, Button, Card, Form, Spinner } from "react-bootstrap";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import { apiClient, setAuthenticated } from "../api";

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fromPath = (location.state as { from?: { pathname?: string } } | null)
    ?.from?.pathname;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await apiClient.login(username, password);
      setAuthenticated();
      navigate(fromPath || "/", { replace: true });
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        setError("Invalid username or password.");
      } else {
        setError("Could not reach the backend. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-vh-100 d-flex align-items-center justify-content-center position-relative"
      style={{
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      }}
    >
      {/* Background overlay for better contrast */}
      <div className="position-absolute top-0 inset-s-0 w-100 h-100 bg-dark opacity-25"></div>

      <Card
        className="shadow-lg border-0 position-relative"
        style={{ width: "100%", maxWidth: "420px", borderRadius: "15px" }}
      >
        <Card.Body className="p-5">
          <div className="text-center mb-4">
            <div className="mb-3">
              <i
                className="bi bi-shield-lock-fill text-primary"
                style={{ fontSize: "3rem" }}
              ></i>
            </div>
            <h2 className="fw-bold text-dark mb-2">Welcome Back</h2>
            <p className="text-muted mb-0">Sign in to LogWatcher</p>
          </div>

          {error && (
            <Alert
              variant="danger"
              className="border-0 shadow-sm mb-4"
              style={{ borderRadius: "10px" }}
            >
              <i className="bi bi-exclamation-triangle-fill me-2"></i>
              {error}
            </Alert>
          )}

          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-4" controlId="username">
              <Form.Label className="fw-semibold text-dark">
                <i className="bi bi-person-fill me-2"></i>Username
              </Form.Label>
              <Form.Control
                type="text"
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
                className="border-0 shadow-sm"
                style={{ borderRadius: "10px", padding: "12px 16px" }}
                placeholder="Enter your username"
              />
            </Form.Group>

            <Form.Group className="mb-4" controlId="password">
              <Form.Label className="fw-semibold text-dark">
                <i className="bi bi-lock-fill me-2"></i>Password
              </Form.Label>
              <Form.Control
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                className="border-0 shadow-sm"
                style={{ borderRadius: "10px", padding: "12px 16px" }}
                placeholder="Enter your password"
              />
            </Form.Group>

            <Button
              type="submit"
              className="w-100 fw-bold border-0 shadow-sm"
              style={{
                borderRadius: "10px",
                padding: "12px",
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                border: "none",
              }}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Spinner size="sm" className="me-2" />
                  Signing in...
                </>
              ) : (
                <>
                  <i className="bi bi-box-arrow-in-right me-2"></i>
                  Sign In
                </>
              )}
            </Button>
          </Form>

          <div className="text-center mt-4">
            <small className="text-muted">
              Secure access to your logging dashboard
            </small>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
};

export default Login;
