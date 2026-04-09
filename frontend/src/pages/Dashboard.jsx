import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Dashboard() {
  const [message, setMessage] = useState("");
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSend = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    try {
      const { data } = await api.post("/orchestrator/run", { message });
      setResponses((prev) => [...prev, { user: message, reply: data.reply }]);
      setMessage("");
    } catch (err) {
      if (err.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/login");
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

      <div style={{ marginTop: "1rem", minHeight: "300px", background: "#fff", padding: "1rem", borderRadius: "8px" }}>
        {responses.map((r, i) => (
          <div key={i} style={{ marginBottom: "1rem" }}>
            <p><strong>You:</strong> {r.user}</p>
            <p><strong>MACE:</strong> {r.reply}</p>
            <hr />
          </div>
        ))}
        {loading && <p>Processing…</p>}
      </div>

      <form onSubmit={handleSend} style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
        <input
          style={{ flex: 1 }}
          placeholder="Describe your task…"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button type="submit" disabled={loading}>Send</button>
      </form>
    </div>
  );
}

export default Dashboard;
