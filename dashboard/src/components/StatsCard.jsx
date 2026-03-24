export default function StatsCard({ label, value, type }) {
  return (
    <div className={`stat-card ${type}`}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  )
}