import  Nav from "react-bootstrap/Nav";
import { NavLink}  from "react-router-dom";
import { RxDashboard } from "react-icons/rx";
import { FaFileAlt} from "react-icons/fa"; 

const Sidebar = () => {
  const linkStyle = {
    padding: "10px 15px",
    borderRadius: "5px",
    marginBottom: "5px",
    display: "flex",
    alignItems: "center",
    gap: "10px", 
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
        justifyContent: "flex-start",
      }}
    >
      <h3 className="mb-4" style={{ color: "#ffc107" }}>
        LogWatcher
      </h3>

      <Nav className="flex-column">
        <Nav.Item>
          <Nav.Link
            as={NavLink}
            to="/"
            end
            style={({ isActive }) => ({
              ...linkStyle,
              color: isActive ? "#343a40" : "white",
              backgroundColor: isActive ? "#ffc107" : "transparent",
              fontWeight: isActive ? "bold" : "normal",
            })}
          >
            <RxDashboard />
            Dashboard
          </Nav.Link>
        </Nav.Item>

        <Nav.Item>
          <Nav.Link
            as={NavLink}
            to="/logs"
            style={({ isActive }) => ({
              ...linkStyle,
              color: isActive ? "#343a40" : "white",
              backgroundColor: isActive ? "#ffc107" : "transparent",
              fontWeight: isActive ? "bold" : "normal",
            })}
          >
            <FaFileAlt /> Logs
          </Nav.Link>
        </Nav.Item>
      </Nav>
    </div>
  );
};

export default Sidebar;
