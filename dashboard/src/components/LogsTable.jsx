export default function LogsTable({ logs }) {
  if (logs.length === 0) {
    return (
      <div className="logs-table">
        <div className="empty">
          Currently there are no logs to show
        </div>
      </div>
    )
  }

  return (
    <div className="logs-table">
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>User</th>
            <th>Role</th>
            <th>Path</th>
            <th>Device</th>
            <th>Status</th>
            <th>Blocked At</th>
            <th>Reason</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.id}>
              <td>{log.timestamp}</td>
              <td>{log.email}</td>
              <td>{log.role}</td>
              <td>{log.path}</td>
              <td>{log.device_id || "—"}</td>
              <td>
                <span className={`badge ${log.allowed ? "allowed" : "blocked"}`}>
                  {log.allowed ? "✓ Allowed" : "✗ Blocked"}
                </span>
              </td>
              <td>
                {log.blocked_at
                  ? <span className="blocked-at">{log.blocked_at}</span>
                  : "—"
                }
              </td>
              <td>{log.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}