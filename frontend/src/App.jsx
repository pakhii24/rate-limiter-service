import { useState, useEffect, useCallback, useRef } from "react"
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import axios from "axios"

const API = "http://localhost:8000"
const WS = "ws://3.109.152.24:8000/ws/metrics"

function StatCard({ label, value, sub, color }) {
  return (
    <div style={{
      background: "#111", border: `1px solid ${color}33`,
      borderRadius: 12, padding: "20px 24px", flex: 1, minWidth: 160
    }}>
      <div style={{ color: "#666", fontSize: 12, marginBottom: 6 }}>{label}</div>
      <div style={{ color, fontSize: 32, fontWeight: 700 }}>{value}</div>
      {sub && <div style={{ color: "#555", fontSize: 11, marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

function LogRow({ log }) {
  return (
    <tr style={{ borderBottom: "1px solid #1a1a1a" }}>
      <td style={{ padding: "10px 12px", color: "#666", fontSize: 12 }}>{log.timestamp?.slice(11, 19)}</td>
      <td style={{ padding: "10px 12px", color: "#aaa", fontSize: 13 }}>{log.user_id || "—"}</td>
      <td style={{ padding: "10px 12px", color: "#aaa", fontSize: 13 }}>{log.ip}</td>
      <td style={{ padding: "10px 12px", color: "#7dd3fc", fontSize: 13 }}>{log.endpoint}</td>
      <td style={{ padding: "10px 12px" }}>
        <span style={{
          background: log.allowed ? "#052e16" : "#2d0a0a",
          color: log.allowed ? "#4ade80" : "#f87171",
          padding: "2px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600
        }}>
          {log.allowed ? "ALLOWED" : "BLOCKED"}
        </span>
      </td>
      <td style={{ padding: "10px 12px", color: "#888", fontSize: 12 }}>{log.algorithm}</td>
    </tr>
  )
}

export default function App() {
  const [logs, setLogs] = useState([])
  const [rules, setRules] = useState([])
  const [chartData, setChartData] = useState([])
  const [wsStatus, setWsStatus] = useState("connecting")
  const [liveMetrics, setLiveMetrics] = useState({ total: 0, allowed: 0, blocked: 0 })
  const [newRule, setNewRule] = useState({ endpoint: "", algorithm: "sliding_window", limit: 60, window_seconds: 60 })
  const [tab, setTab] = useState("overview")
  const wsRef = useRef(null)

  // WebSocket for live metrics
  useEffect(() => {
    function connect() {
      const ws = new WebSocket(WS)
      wsRef.current = ws

      ws.onopen = () => setWsStatus("live")

      ws.onmessage = (e) => {
        const data = JSON.parse(e.data)
        setLiveMetrics(data)
        setChartData(prev => {
          const point = {
            time: new Date().toLocaleTimeString(),
            allowed: data.allowed,
            blocked: data.blocked
          }
          return [...prev.slice(-20), point]
        })
      }

      ws.onclose = () => {
        setWsStatus("reconnecting")
        setTimeout(connect, 2000)
      }

      ws.onerror = () => {
        setWsStatus("error")
        ws.close()
      }
    }

    connect()
    return () => wsRef.current?.close()
  }, [])

  const fetchLogs = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/logs?limit=50`)
      setLogs(res.data.logs)
    } catch (e) { console.error(e) }
  }, [])

  const fetchRules = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/rules`)
      setRules(res.data.rules)
    } catch (e) { console.error(e) }
  }, [])

  useEffect(() => {
    fetchLogs()
    fetchRules()
    const interval = setInterval(fetchLogs, 5000)
    return () => clearInterval(interval)
  }, [fetchLogs, fetchRules])

  const createRule = async () => {
    try {
      await axios.post(`${API}/rules`, null, { params: newRule })
      fetchRules()
      setNewRule({ endpoint: "", algorithm: "sliding_window", limit: 60, window_seconds: 60 })
    } catch (e) { console.error(e) }
  }

  const blockRate = liveMetrics.total ? ((liveMetrics.blocked / liveMetrics.total) * 100).toFixed(1) : 0

  const wsColor = wsStatus === "live" ? "#4ade80" : wsStatus === "reconnecting" ? "#fbbf24" : "#f87171"

  const tabStyle = (t) => ({
    padding: "8px 20px", borderRadius: 8, cursor: "pointer", fontSize: 13, fontWeight: 500,
    background: tab === t ? "#1a1a1a" : "transparent",
    color: tab === t ? "#fff" : "#666", border: "none"
  })

  return (
    <div style={{ background: "#0a0a0a", minHeight: "100vh", color: "#fff", fontFamily: "monospace" }}>
      <div style={{ borderBottom: "1px solid #1a1a1a", padding: "16px 32px", display: "flex", alignItems: "center", gap: 16 }}>
        <div style={{ width: 8, height: 8, borderRadius: "50%", background: wsColor }} />
        <span style={{ fontWeight: 700, fontSize: 16 }}>Rate Limiter</span>
        <span style={{ color: "#333", fontSize: 12 }}>— admin dashboard</span>
        <div style={{ marginLeft: "auto", color: wsColor, fontSize: 11 }}>
          ● {wsStatus === "live" ? "websocket live" : wsStatus}
        </div>
      </div>

      <div style={{ padding: "24px 32px" }}>
        <div style={{ display: "flex", gap: 4, marginBottom: 24 }}>
          <button style={tabStyle("overview")} onClick={() => setTab("overview")}>Overview</button>
          <button style={tabStyle("logs")} onClick={() => setTab("logs")}>Request logs</button>
          <button style={tabStyle("rules")} onClick={() => setTab("rules")}>Rules</button>
        </div>

        {tab === "overview" && (
          <>
            <div style={{ display: "flex", gap: 16, marginBottom: 32, flexWrap: "wrap" }}>
              <StatCard label="Total requests" value={liveMetrics.total} color="#7dd3fc" />
              <StatCard label="Allowed" value={liveMetrics.allowed} color="#4ade80" />
              <StatCard label="Blocked" value={liveMetrics.blocked} color="#f87171" />
              <StatCard label="Block rate" value={`${blockRate}%`} color="#fbbf24" />
              <StatCard label="Active rules" value={rules.length} color="#c084fc" />
            </div>

            <div style={{ background: "#111", borderRadius: 12, padding: 24, border: "1px solid #1a1a1a" }}>
              <div style={{ color: "#666", fontSize: 12, marginBottom: 16 }}>allowed vs blocked — websocket live</div>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
                  <XAxis dataKey="time" stroke="#333" tick={{ fontSize: 10, fill: "#555" }} />
                  <YAxis stroke="#333" tick={{ fontSize: 10, fill: "#555" }} />
                  <Tooltip contentStyle={{ background: "#111", border: "1px solid #333", borderRadius: 8 }} />
                  <Line type="monotone" dataKey="allowed" stroke="#4ade80" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="blocked" stroke="#f87171" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </>
        )}

        {tab === "logs" && (
          <div style={{ background: "#111", borderRadius: 12, border: "1px solid #1a1a1a", overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #1a1a1a" }}>
                  {["time", "user", "ip", "endpoint", "status", "algorithm"].map(h => (
                    <th key={h} style={{ padding: "10px 12px", color: "#444", fontSize: 11, textAlign: "left", fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {logs.map(log => <LogRow key={log.id} log={log} />)}
              </tbody>
            </table>
          </div>
        )}

        {tab === "rules" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            <div style={{ background: "#111", borderRadius: 12, border: "1px solid #1a1a1a", overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #1a1a1a" }}>
                    {["endpoint", "algorithm", "limit", "window (s)"].map(h => (
                      <th key={h} style={{ padding: "10px 12px", color: "#444", fontSize: 11, textAlign: "left" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rules.map(r => (
                    <tr key={r.id} style={{ borderBottom: "1px solid #1a1a1a" }}>
                      <td style={{ padding: "10px 12px", color: "#7dd3fc", fontSize: 13 }}>{r.endpoint}</td>
                      <td style={{ padding: "10px 12px", color: "#aaa", fontSize: 13 }}>{r.algorithm}</td>
                      <td style={{ padding: "10px 12px", color: "#4ade80", fontSize: 13 }}>{r.limit}</td>
                      <td style={{ padding: "10px 12px", color: "#aaa", fontSize: 13 }}>{r.window_seconds}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ background: "#111", borderRadius: 12, border: "1px solid #1a1a1a", padding: 24 }}>
              <div style={{ color: "#666", fontSize: 12, marginBottom: 16 }}>create new rule</div>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <label style={{ color: "#555", fontSize: 11 }}>endpoint</label>
                  <input
                    value={newRule.endpoint}
                    onChange={e => setNewRule(p => ({ ...p, endpoint: e.target.value }))}
                    placeholder="/api/products"
                    style={{ background: "#0a0a0a", border: "1px solid #222", borderRadius: 6, padding: "8px 12px", color: "#fff", fontSize: 13, width: 200 }}
                  />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <label style={{ color: "#555", fontSize: 11 }}>algorithm</label>
                  <select value={newRule.algorithm} onChange={e => setNewRule(p => ({ ...p, algorithm: e.target.value }))}
                    style={{ background: "#0a0a0a", border: "1px solid #222", borderRadius: 6, padding: "8px 12px", color: "#fff", fontSize: 13 }}>
                    <option value="sliding_window">sliding_window</option>
                    <option value="token_bucket">token_bucket</option>
                  </select>
                </div>
                {[{ key: "limit", label: "limit" }, { key: "window_seconds", label: "window (s)" }].map(f => (
                  <div key={f.key} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <label style={{ color: "#555", fontSize: 11 }}>{f.label}</label>
                    <input type="number" value={newRule[f.key]}
                      onChange={e => setNewRule(p => ({ ...p, [f.key]: parseInt(e.target.value) }))}
                      style={{ background: "#0a0a0a", border: "1px solid #222", borderRadius: 6, padding: "8px 12px", color: "#fff", fontSize: 13, width: 80 }}
                    />
                  </div>
                ))}
                <button onClick={createRule} style={{
                  background: "#4ade80", color: "#000", border: "none", borderRadius: 6,
                  padding: "8px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer"
                }}>
                  + create
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}