import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import Spinner from "../components/Spinner";

function Dashboard() {
  const [message, setMessage] = useState("");
  const [responses, setResponses] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);
  const navigate = useNavigate();

  const fetchTasks = async () => {
    try {
      const { data } = await api.get("/orchestrator/tasks");
      setTasks(data);
    } catch (err) {
      if (err.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/login");
      }
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [responses, loading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    try {
      const { data } = await api.post("/orchestrator/run", { message });
      setResponses((prev) => [
        ...prev,
        {
          user: message,
          reply: data.reply,
          tasks: data.tasks || [],
          conflicts: data.conflicts || [],
        },
      ]);
      setMessage("");
      fetchTasks();
    } catch (err) {
      if (err.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/login");
      } else {
        setResponses((prev) => [
          ...prev,
          {
            user: message,
            reply: "Error: " + (err.response?.data?.detail || "Request failed"),
            tasks: [],
            conflicts: [],
          },
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  const getPriorityClass = (p) => {
    if (p === "high") return "tag-priority-high";
    if (p === "low") return "tag-priority-low";
    return "tag-priority-medium";
  };

  return (
    <div className="dashboard-layout">
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-brand">
          <h1>MACE</h1>
          <span className="navbar-badge">Online</span>
        </div>
        <button className="btn-danger" onClick={handleLogout}>
          Sign out
        </button>
      </nav>

      {/* Chat Area */}
      <div className="chat-container">
        {responses.length === 0 && !loading && (
          <div className="chat-empty">
            <div className="chat-empty-icon">⚡</div>
            <p>Welcome to MACE</p>
            <small>Describe a task and the AI agents will handle it for you.</small>
          </div>
        )}

        {responses.map((r, i) => (
          <div key={i}>
            {/* User message */}
            <div className="msg msg-user">
              <span className="msg-label">You</span>
              <div className="msg-bubble">{r.user}</div>
            </div>

            {/* Assistant message */}
            <div className="msg msg-assistant">
              <span className="msg-label">MACE</span>
              <div className="msg-bubble">{r.reply}</div>
              {r.tasks.length > 0 && (
                <div className="msg-meta">
                  {r.tasks.map((t, j) => (
                    <span key={j}>
                      <span className="tag tag-agent">🤖 {t.assigned_agent}</span>
                      {t.intent_type && <span className="tag tag-intent">{t.intent_type}</span>}
                      {t.priority && (
                        <span className={`tag ${getPriorityClass(t.priority)}`}>{t.priority}</span>
                      )}
                    </span>
                  ))}
                </div>
              )}
              {r.tasks.length > 0 && r.tasks[0].tools_used && (
                <div className="msg-tools">
                  Tools: {r.tasks[0].tools_used.join(" → ")}
                </div>
              )}
              {r.conflicts.length > 0 && (
                <div className="msg-meta">
                  {r.conflicts.map((c, j) => (
                    <span key={j} className="tag tag-conflict">
                      ⚠ {c.type} — {c.resolution}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="processing">
            <Spinner size={18} />
            Agents are processing your request…
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Bar */}
      <form className="input-bar" onSubmit={handleSend}>
        <input
          placeholder="Describe your task — e.g. 'Reset my password' or 'How do I configure VPN?'"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button type="submit" className="btn-send" disabled={loading}>
          {loading ? <Spinner size={16} /> : "Send"}
        </button>
      </form>

      {/* Task History */}
      {tasks.length > 0 && (
        <div className="task-section">
          <h2>Task History</h2>
          <table className="task-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Intent</th>
                <th>Agent</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id}>
                  <td>#{t.id}</td>
                  <td>{t.intent}</td>
                  <td>
                    <span className="agent-badge">🤖 {t.assigned_agent}</span>
                  </td>
                  <td>
                    <span
                      className={`status-badge ${
                        t.status === "completed" ? "status-completed" : "status-pending"
                      }`}
                    >
                      {t.status === "completed" ? "✓" : "●"} {t.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
