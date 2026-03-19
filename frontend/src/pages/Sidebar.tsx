import Nav from "react-bootstrap/Nav";
import Button from "react-bootstrap/Button";
import { NavLink, useNavigate } from "react-router-dom";
import { RxDashboard } from "react-icons/rx";
import { FaFileAlt } from "react-icons/fa";
import { BiBarChartAlt2 } from "react-icons/bi";
import { type CSSProperties } from "react";
import { clearAuthenticated } from "../api";

const Sidebar = () => {
  const navigate = useNavigate();

  const linkStyle: CSSProperties = {
    padding: "10px 15px",
    borderRadius: "5px",
    marginBottom: "5px",
    display: "flex",
    alignItems: "center",
    gap: "10px", 
  };

  const getNavLinkStyle = (isActive: boolean): CSSProperties => ({
    ...linkStyle,
    color: isActive ? "#343a40" : "white",
    backgroundColor: isActive ? "#ffc107" : "transparent",
    fontWeight: isActive ? "bold" : "normal",
  });

  const handleLogout = () => {
    clearAuthenticated();
    navigate("/login", { replace: true });
  };

  return (
    <div
      style={{
        width: "220px",
        height: "100vh",
        backgroundColor: "#343a40",
        color: "white",
        padding: "20px",
        position: "fixed",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      <div>
        <h3 className="mb-4" style={{ color: "#ffc107" }}>
          LogWatcher
        </h3>

        <Nav className="flex-column">
          <Nav.Item>
            <NavLink
              to="/"
              end
              style={({ isActive }) => getNavLinkStyle(isActive)}
            >
              <RxDashboard />
              Dashboard
            </NavLink>
          </Nav.Item>

          <Nav.Item>
            <NavLink
              to="/logs"
              style={({ isActive }) => getNavLinkStyle(isActive)}
            >
              <FaFileAlt /> Logs
            </NavLink>
          </Nav.Item>

          <Nav.Item>
            <NavLink
              to="/analytics"
              style={({ isActive }) => getNavLinkStyle(isActive)}
            >
              <BiBarChartAlt2 /> Analytics
            </NavLink>
          </Nav.Item>
        </Nav>
      </div>

      <Button variant="outline-light" onClick={handleLogout}>
        Logout
      </Button>
    </div>
  );
};

export default Sidebar;
