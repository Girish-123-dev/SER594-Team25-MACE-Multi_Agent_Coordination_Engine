import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import Spinner from "../components/Spinner";

function Dashboard() {
  const [message, setMessage] = useState("");
  const [responses, setResponses] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
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

  return (
    <div className="container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>MACE Dashboard</h1>
        <button onClick={handleLogout} style={{ background: "#666" }}>
          Logout
        </button>
      </div>

      <div
        style={{
          marginTop: "1rem",
          minHeight: "300px",
          background: "#fff",
          padding: "1rem",
          borderRadius: "8px",
        }}
      >
        {responses.map((r, i) => (
          <div key={i} style={{ marginBottom: "1rem" }}>
            <p>
              <strong>You:</strong> {r.user}
            </p>
            <p>
              <strong>MACE:</strong> {r.reply}
            </p>
            {r.tasks.length > 0 && (
              <div style={{ marginLeft: "1rem", fontSize: "0.9rem", color: "#555" }}>
                {r.tasks.map((t, j) => (
                  <p key={j}>
                    Task #{t.task_id} — {t.intent_type} → {t.assigned_agent} agent [{t.priority}]
                  </p>
                ))}
              </div>
            )}
            {r.conflicts.length > 0 && (
              <div style={{ marginLeft: "1rem", fontSize: "0.9rem", color: "#d32f2f" }}>
                {r.conflicts.map((c, j) => (
                  <p key={j}>
                    Conflict: {c.type} — {c.resolution}
                  </p>
                ))}
              </div>
            )}
            <hr />
          </div>
        ))}
        {loading && (
          <p>
            <Spinner size={18} /> Processing…
          </p>
        )}
      </div>

      <form onSubmit={handleSend} style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
        <input
          style={{ flex: 1 }}
          placeholder="Describe your task…"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          Send
        </button>
      </form>

      {tasks.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h2>Task History</h2>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              background: "#fff",
              borderRadius: "8px",
            }}
          >
            <thead>
              <tr style={{ borderBottom: "2px solid #ddd", textAlign: "left" }}>
                <th style={{ padding: "0.5rem" }}>ID</th>
                <th style={{ padding: "0.5rem" }}>Intent</th>
                <th style={{ padding: "0.5rem" }}>Agent</th>
                <th style={{ padding: "0.5rem" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: "0.5rem" }}>#{t.id}</td>
                  <td style={{ padding: "0.5rem" }}>{t.intent}</td>
                  <td style={{ padding: "0.5rem" }}>{t.assigned_agent}</td>
                  <td style={{ padding: "0.5rem" }}>{t.status}</td>
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
