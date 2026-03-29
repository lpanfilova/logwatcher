import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
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
    <div className="max-w-7xl mx-auto p-4">
      {/* Header */}
      <div className="shadow-lg border-0 mb-4 rounded-2xl bg-[linear-gradient(135deg,#667eea_0%,#764ba2_100%)] text-white p-6 flex justify-between items-center">
        <div className="flex items-center">
          <span className="text-3xl me-4">📄</span>
          <div>
            <h2 className="font-bold text-2xl mb-0">Log Details</h2>
            <small className="opacity-75">Detailed view of log entry</small>
          </div>
        </div>
        <Link to="/logs">
          <button className="rounded-lg font-semibold text-white bg-white bg-opacity-10 border border-white border-opacity-30 px-4 py-2 transition hover:bg-opacity-20">
            ← Back to Logs
          </button>
        </Link>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="shadow-lg rounded-2xl bg-white backdrop-blur-md">
          <div className="p-12 text-center">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <h5 className="text-gray-500 mb-2">Loading Log Details</h5>
            <p className="text-gray-500 text-sm">
              Fetching detailed information for log entry...
            </p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="rounded-xl bg-[linear-gradient(135deg,#f8d7da_0%,#f5c6cb_100%)] border border-red-500 p-4 shadow-sm mb-4 flex items-center">
          <span className="text-red-600 text-xl me-3">⚠️</span>
          <div>
            <strong>Error:</strong> {error}
          </div>
        </div>
      )}

      {/* Log Details */}
      {!loading && log && (
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-8">
            <div className="shadow-lg rounded-2xl bg-white backdrop-blur-md">
              <div className="p-6">
                {/* Message Section */}
                <div className="mb-6">
                  <div className="flex items-center mb-4">
                    <span className="text-2xl me-3">💬</span>
                    <h4 className="font-bold text-lg text-gray-800 mb-0">
                      Log Message
                    </h4>
                  </div>
                  <div className="p-4 rounded-lg bg-[linear-gradient(135deg,#f8f9fa_0%,#e9ecef_100%)] border border-black border-opacity-5">
                    <p className="mb-0 break-all text-base leading-relaxed">
                      {log.msg || log.message}
                    </p>
                  </div>
                </div>

                <hr className="my-6 border-black border-opacity-10" />

                {/* Metadata Section */}
                <div className="mb-6">
                  <div className="flex items-center mb-4">
                    <span className="text-2xl me-3">ℹ️</span>
                    <h4 className="font-bold text-lg text-gray-800 mb-0">
                      Metadata
                    </h4>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="col-span-4">
                      <div className="p-3 rounded-lg shadow-sm bg-white border border-gray-200">
                        <div className="flex items-center mb-2">
                          <span className="text-gray-500 me-2">#</span>
                          <small className="text-gray-500 font-semibold">
                            ID
                          </small>
                        </div>
                        <div className="font-medium text-sm">{log.id}</div>
                      </div>
                    </div>
                    <div>
                      <div className="p-3 rounded-lg shadow-sm bg-white border border-gray-200">
                        <div className="flex items-center mb-2">
                          <span className="text-gray-500 me-2">📅</span>
                          <small className="text-gray-500 font-semibold">
                            Timestamp
                          </small>
                        </div>
                        <div className="font-medium text-sm">
                          {formatTimestamp(log.timestamp)}
                        </div>
                      </div>
                    </div>
                    <div>
                      <div className="p-3 rounded-lg shadow-sm bg-white border border-gray-200">
                        <div className="flex items-center mb-2">
                          <span className="text-gray-500 ">🖥️</span>
                          <small className="text-gray-500 font-semibold">
                            Service
                          </small>
                        </div>
                        <div className="font-medium text-sm">{log.service}</div>
                      </div>
                    </div>
                    <div>
                      <div className="p-3 rounded-lg shadow-sm bg-white border border-gray-200">
                        <div className="flex items-center mb-2">
                          <span className="text-gray-500 me-2">📍</span>
                          <small className="text-gray-500 font-semibold">
                            Source
                          </small>
                        </div>
                        <div className="font-medium text-sm">{log.source}</div>
                      </div>
                    </div>
                    <div>
                      <div className="p-3 rounded-lg shadow-sm bg-white border border-gray-200">
                        <div className="flex items-center mb-2">
                          <span className="text-gray-500 me-2">⚡</span>
                          <small className="text-gray-500 font-semibold">
                            Level
                          </small>
                        </div>
                        <div className="flex items-center">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-semibold ${
                              log.level >= 50
                                ? "bg-red-500 text-white"
                                : log.level >= 40
                                  ? "bg-yellow-500 text-gray-900"
                                  : log.level >= 30
                                    ? "bg-blue-500 text-white"
                                    : "bg-gray-500 text-white"
                            }`}
                          >
                            {mapLogLevelToString(log.level)}
                          </span>
                        </div>
                      </div>
                    </div>
                    {log.event && (
                      <div>
                        <div className="p-3 rounded-lg shadow-sm bg-white border border-gray-200">
                          <div className="flex items-center mb-2">
                            <span className="text-gray-500 me-2">⚙️</span>
                            <small className="text-gray-500 font-semibold">
                              Event
                            </small>
                          </div>
                          <div className="font-medium text-sm">{log.event}</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <hr className="my-6 border-black border-opacity-10" />

                {/* Raw Message Section */}
                <div>
                  <div className="flex items-center mb-4">
                    <span className="text-2xl me-3">{"</>"}</span>
                    <h4 className="font-bold text-lg text-gray-800 mb-0">
                      Raw Message
                    </h4>
                  </div>
                  <div className="p-4 rounded-lg bg-[linear-gradient(135deg,#2d3748_0%,#1a202c_100%)] border border-black border-opacity-10 relative">
                    <pre
                      className="mb-0 text-gray-100 text-sm break-all whitespace-pre-wrap"
                      style={{
                        fontFamily:
                          "Monaco, 'Bitstream Vera Sans Mono', 'Lucida Console', Terminal, monospace",
                        lineHeight: "1.5",
                      }}
                    >
                      {log.message}
                    </pre>
                    <div className="absolute top-2 right-2">
                      <span className="text-white opacity-50">{"</>"}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LogDetails;
