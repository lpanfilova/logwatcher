import { Col, Container, Row, Table } from "react-bootstrap";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler } from "chart.js";
import { useEffect, useState } from "react";
import { apiClient, type LogEntry, type SummaryData, mapLogLevelToString, formatTimestamp } from "../api";
import { getMockLogs, getMockErrorTrend, countIncidents } from "../mockData.ts";
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

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
        fill: true,
        backgroundColor: "rgba(93, 171, 190, 0.2)",
        borderColor: "rgb(75, 126, 192)",
        tension: 0.1,
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

        // Fetch timeline data for the chart
        const timelineResponse = await apiClient.getTimelineMetrics('1h');

        // Update chart data
        setChartData({
          labels: timelineResponse.data.map(point => {
            const date = new Date(point.timestamp);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          }),
          datasets: [
            {
              label: "Log Events",
              data: timelineResponse.data.map(point => point.count),
              fill: true,
              backgroundColor: "rgba(93, 171, 190, 0.2)",
              borderColor: "rgb(75, 126, 192)",
              tension: 0.1,
            },
          ],
        });

        // Fetch recent logs
        const logsResponse = await apiClient.getLogs({ size: 10, min_level: 30 }); // Get recent logs with warnings/errors
        setLogs(logsResponse.logs);

      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
        setError("Failed to load dashboard data");

        // Fallback to mock data
        const mockLogs = getMockLogs();
        const mockTrend = getMockErrorTrend();
        setLogs(mockLogs.map(log => ({
          id: Math.random().toString(),
          timestamp: log.time,
          message: log.message,
          service: log.service,
          source: 'stdout',
          level: log.level === 'ERROR' ? 50 : log.level === 'WARNING' ? 40 : 30,
          msg: log.message
        })));
        setChartData({
          labels: mockTrend.labels,
          datasets: [
            {
              label: "Log Events",
              data: mockTrend.value,
              fill: true,
              backgroundColor: "rgba(93, 171, 190, 0.2)",
              borderColor: "rgb(75, 126, 192)",
              tension: 0.1,
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
  const incidentCounts = countIncidents(logs.map(log => ({
    time: formatTimestamp(log.timestamp),
    service: log.service,
    level: mapLogLevelToString(log.level),
    message: log.msg || log.message
  })));

  //Chart data
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
  };

  return (
    <Container fluid className="p-4">
      {/* Header */}
      <div className="shadow rounded border bg-white mb-4">
        <h3 className="text-center p-3">
          Dashboard
          {summary && (
            <small className="text-muted d-block">
              Total Logs: {summary.total_logs} | Services: {summary.services.length}
            </small>
          )}
        </h3>
      </div>

      {error && (
        <div className="alert alert-warning mb-4">
          {error} - Showing mock data as fallback.
        </div>
      )}

      {/* Top Section */}
      <Row className="g-4 mb-4">
        <Col md={7}>
          <div className="shadow rounded border bg-white p-3 h-100">
            <h4 className="mb-3">Recent Logs</h4>
            {loading ? (
              <div className="text-center py-4">Loading logs...</div>
            ) : (
              <Table striped bordered hover className="mb-0">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Service</th>
                    <th>Level</th>
                    <th>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.slice(0, 6).map((log) => (
                    <tr key={log.id}>
                      <td>{formatTimestamp(log.timestamp)}</td>
                      <td>{log.service}</td>
                      <td>
                        <span className={`badge ${
                          log.level >= 50 ? 'bg-danger' :
                          log.level >= 40 ? 'bg-warning' :
                          log.level >= 30 ? 'bg-info' : 'bg-secondary'
                        }`}>
                          {mapLogLevelToString(log.level)}
                        </span>
                      </td>
                      <td>{log.msg || log.message}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </div>
        </Col>

        <Col md={5}>
          <div className="shadow rounded border bg-white p-3">
            <h4 className="mb-3">Incidents</h4>
            <div style={{ maxHeight: "300px", overflow: "auto", overflowX: "hidden" }}>
              {Object.entries(incidentCounts).map(([incident, count]) => (
                <div className="border rounded p-2 mb-2" key={incident}>
                  <strong>{incident}</strong>
                  <div className="text-muted">Occurrences: {count}</div>
                </div>
              ))}
            </div>
          </div>
        </Col>
      </Row>

      {/* Bottom Section */}
      <Row className="g-4">
        <Col>
          <div className="shadow rounded border bg-white p-3" style={{ height: "500px" }}>
            <h3 className="mb-3">Log Events Timeline</h3>
            <div className="border rounded p-3 mb-3" style={{ height: "400px" }}>
              {loading ? (
                <div className="text-center py-4">Loading chart data...</div>
              ) : (
                <Line data={chartData} options={chartOptions} />
              )}
            </div>
          </div>
        </Col>
      </Row>
    </Container>
  );
};

export default Dashboard;
