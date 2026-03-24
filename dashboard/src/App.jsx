import { useEffect, useState } from "react"
import axios from "axios"
import StatsCard from "./components/StatsCard"
import LogsTable from "./components/LogsTable"
import ServiceStatus from "./components/ServiceStatus"

export default function App() {
  const [logs, setLogs]   = useState([])
  const [stats, setStats] = useState({
    total_requests: 0,
    allowed: 0,
    blocked: 0,
    block_rate: "0%"
  })

  async function fetchData() {
    try {
      const [logsRes, statsRes] = await Promise.all([
        axios.get("http://localhost:9999/logs"),
        axios.get("http://localhost:9999/stats"),
      ])
      setLogs(logsRes.data)
      setStats(statsRes.data)
    } catch (err) {
      console.error("Audit service se data nahi aaya:", err)
    }
  }

  useEffect(() => {
    fetchData()
    // Har 5 second mein auto refresh
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div>
      {/* NAVBAR */}
      <div className="navbar">
        <h1>⚡ GateKeeper Dashboard</h1>
        <div className="live-badge">
          <div className="live-dot" />
          Live — auto refresh 5s
        </div>
      </div>

      <div className="container">

        {/* STATS */}
        <div className="stats-grid">
          <StatsCard
            label="Total Requests"
            value={stats.total_requests}
            type="total"
          />
          <StatsCard
            label="Allowed"
            value={stats.allowed}
            type="allowed"
          />
          <StatsCard
            label="Blocked"
            value={stats.blocked}
            type="blocked"
          />
          <StatsCard
            label="Block Rate"
            value={stats.block_rate}
            type="rate"
          />
        </div>

        {/* SERVICES STATUS */}
        <ServiceStatus />

        {/* LOGS TABLE */}
        <div className="logs-header">
          <div className="section-title">Access Logs</div>
          <button className="refresh-btn" onClick={fetchData}>
            ↻ Refresh
          </button>
        </div>
        <LogsTable logs={logs} />

      </div>
    </div>
  )
}
