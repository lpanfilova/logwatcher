import { NavLink, useNavigate } from "react-router-dom";
import {
  MdDashboard,
  MdOutlineArticle,
  MdAnalytics,
  MdChat,
  MdSecurity,
  MdLogout,
} from "react-icons/md";
import { clearAuthenticated } from "../api";

const Sidebar = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    clearAuthenticated();
    navigate("/login", { replace: true });
  };

  return (
    <div className="w-60 h-screen bg-[linear-gradient(135deg,#667eea_0%,#764ba2_100%)] text-white p-6 fixed flex flex-col justify-between shadow-[4px_0_15px_rgba(0,0,0,0.1)] backdrop-blur-[10px]">
      <div>
        <div className="flex items-center mb-5">
          <div className="rounded-full flex items-center justify-center mr-3 w-12 h-12 bg-[rgba(255,255,255,0.2)] border-2 border-[rgba(255,255,255,0.3)]">
            <MdSecurity className="text-xl text-white" />
          </div>
          <div>
            <h4 className="mb-0 font-bold text-white ">LogWatcher</h4>
            <small className="text-[rgba(255,255,255,0.7)]">
              Monitoring Suite
            </small>
          </div>
        </div>

        <div className="flex flex-col">
          <div className="mb-2">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `flex items-center gap-3 p-3 rounded-xl mb-2 transition-all duration-50 font-medium ${
                  isActive
                    ? "text-white bg-[rgba(255,255,255,0.2)] border border-[rgba(255,255,255,0.3)] font-semibold translate-x-1"
                    : "text-white hover:opacity-80 hover:border"
                }`
              }
            >
              <MdDashboard className="text-xl" />
              <span>Dashboard</span>
            </NavLink>
          </div>

          <div className="mb-2">
            <NavLink
              to="/logs"
              className={({ isActive }) =>
                `flex items-center gap-3 p-3 rounded-xl mb-2 transition-all duration-50 font-medium ${
                  isActive
                    ? "text-white bg-[rgba(255,255,255,0.2)] border border-[rgba(255,255,255,0.3)] font-semibold translate-x-1"
                    : "text-white hover:opacity-80 hover:border"
                }`
              }
            >
              <MdOutlineArticle className="text-xl" />
              <span>Logs</span>
            </NavLink>
          </div>

          <div className="mb-2">
            <NavLink
              to="/analytics"
              className={({ isActive }) =>
                `flex items-center gap-3 p-3 rounded-xl mb-2 transition-all duration-50 font-medium ${
                  isActive
                    ? "text-white bg-[rgba(255,255,255,0.2)] border border-[rgba(255,255,255,0.3)] font-semibold translate-x-1"
                    : "text-white hover:opacity-80 hover:border"
                }`
              }
            >
              <MdAnalytics className="text-xl" />
              <span>Analytics</span>
            </NavLink>
          </div>

          <div className="mb-2">
            <NavLink
              to="/chat"
              className={({ isActive }) =>
                `flex items-center gap-3 p-3 rounded-xl mb-2 transition-all duration-50 font-medium ${
                  isActive
                    ? "text-white bg-[rgba(255,255,255,0.2)] border border-[rgba(255,255,255,0.3)] font-semibold translate-x-1"
                    : "text-white hover:opacity-80 hover:border"
                }`
              }
            >
              <MdChat className="text-xl" />
              <span>AI Chat</span>
            </NavLink>
          </div>
        </div>
      </div>

      <div className="mt-auto">
        <div className="border-t border-white border-opacity-25 mb-3 rounded-full"></div>
        <div className="hover:bg-white hover:text-black bg-opacity-25 border border-white border-opacity-50 rounded-lg transition-all duration-50 ease-in-out hover:bg-opacity-30 hover:-translate-y-0.5 ">
          <button
            onClick={handleLogout}
            className="w-full font-semibold  p-3 flex items-center"
          >
            <MdLogout className="mr-2 text-base" />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
