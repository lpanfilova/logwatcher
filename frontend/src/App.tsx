import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Logs from "./pages/Logs";
import LogDetails from "./pages/LogDetails";
import Analytics from "./pages/Analytics";
import Chat from "./pages/Chat";
import Sidebar from "./pages/Sidebar";
import Login from "./pages/Login";
import { isAuthenticated } from "./api";

const AppLayout = () => {
  return (
    <div style={{ display: "flex" }}>
      <Sidebar />
      <div style={{ marginLeft: "220px", padding: "20px", width: "100%" }}>
        <Outlet />
      </div>
    </div>
  );
};

const ProtectedRoute = () => {
  const location = useLocation();

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <AppLayout />;
};

const LoginRoute = () => {
  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }

  return <Login />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginRoute />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/logs/:id" element={<LogDetails />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/chat" element={<Chat />} />
        </Route>
        <Route
          path="*"
          element={<Navigate to={isAuthenticated() ? "/" : "/login"} replace />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
