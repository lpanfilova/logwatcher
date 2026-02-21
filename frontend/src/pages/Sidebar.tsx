import Nav from "react-bootstrap/Nav";
import { NavLink } from "react-router-dom";
import { RxDashboard } from "react-icons/rx";
import { FaFileAlt } from "react-icons/fa";
import {type CSSProperties } from "react";

const Sidebar = () => {
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
        justifyContent: "flex-start",
      }}
    >
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
      </Nav>
    </div>
  );
};

export default Sidebar;
