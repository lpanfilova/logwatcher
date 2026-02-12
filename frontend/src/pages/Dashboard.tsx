import { Col, Container, Row, Table } from "react-bootstrap";
import { Line } from "react-chartjs-2"; 
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler } from "chart.js";
import { useEffect, useState } from "react";
import axios from "axios";
import { getMockLogs, getMockErrorTrend, countIncidents } from "../mockData.ts";
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler); 

const Dashboard = () => {
  const [logs, setLogs] = useState(getMockLogs());
  const mockErrorTrend = getMockErrorTrend();
  const [chartData, setChartData] = useState({
    labels: mockErrorTrend.labels,
    datasets: [
      {
        label: "Errors",
        data: mockErrorTrend.value, 
        fill: true, 
        backgroundColor: "rgba(93, 171, 190, 0.2)",
        borderColor: "rgb(75, 126, 192)",
        tension: 0.1, 
      },
    ],
  });

  useEffect(() => {
    axios
      .get("http://localhost:5000/dashboard/errors")
      .then((res) => {
        setChartData({
          labels: res.data.labels,
          datasets: [
            {
              label: "Errors",
              data: res.data.value, 
              fill: true,
              backgroundColor: "rgba(93, 171, 190, 0.2)",
              borderColor: "rgb(75, 126, 192)",
              tension: 0.1, 
            },
          ],
        });
      })
      .catch((err) => {
        console.error("Failed to fetch error trend, using mock data:", err);
        // Use mock data as fallback
        const mockData = getMockErrorTrend();
        setChartData({
          labels: mockData.labels,
          datasets: [
            {
              label: "Errors",
              data: mockData.value, 
              fill: true,
              backgroundColor: "rgba(93, 171, 190, 0.2)",
              borderColor: "rgb(75, 126, 192)",
              tension: 0.1, 
            },
          ],
        });
      });
  }, []);


  useEffect(() => {
    axios
      .get("http://localhost:5000/dashboard/logs") 
      .then((res) => setLogs(res.data))
      .catch((err) => {
        console.error("Failed to fetch logs, using mock data:", err);
        // Use mock data as fallback
        setLogs(getMockLogs());
      });
  }, []);

  // Count occurrences of each incident message dynamically
  const incidentCounts = countIncidents(logs);

  //Chart data
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
  };

  return (
    <Container fluid className="p-4">
      {/* Header */}
      <div className="shadow rounded border bg-white mb-4">
        <h3 className="text-center p-3">Dashboard</h3>
      </div>

      {/* Top Section */}
      <Row className="g-4 mb-4">
        <Col md={7}>
          <div className="shadow rounded border bg-white p-3 h-100">
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
                {logs.slice(0, 6).map(
                  (
                    log,
                    index //To show the first 6 log records
                  ) => (
                    <tr key={index}>
                      <td>{log.time}</td>
                      <td>{log.service}</td>
                      <td>{log.level}</td>
                      <td>{log.message}</td>
                    </tr>
                  )
                )}
              </tbody>
            </Table>
          </div>
        </Col>

        <Col md={5}>
          <div className="shadow rounded border bg-white p-3 ">
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
            <h3 className="mb-3">Error Trend</h3>
            <div className="border rounded p-3 mb-3" style={{ height: "400px" }}>
              {/* Line comes from react-chartjs-2 , convert chartData into a canvas chart*/}
              <Line data={chartData} options={chartOptions} />
            </div>
          </div>
        </Col>
      </Row>
    </Container>
  );
};

export default Dashboard;
