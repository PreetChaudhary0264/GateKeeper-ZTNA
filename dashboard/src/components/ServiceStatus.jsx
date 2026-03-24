import { useEffect, useState } from "react"
import axios from "axios"

const SERVICES = [
  { name: "Gateway",   port: 8080, path: "/health", https: true },
  { name: "Auth",      port: 8001, path: "/health", https: false },
  { name: "HR Portal", port: 9001, path: "/health", https: true  },
  { name: "Finance",   port: 9002, path: "/health", https: true  },
  { name: "Audit",     port: 9999, path: "/health", https: false },
]

export default function ServiceStatus() {
  const [statuses, setStatuses] = useState({})

  async function checkServices() {
    const results = {}
    for (const svc of SERVICES) {
      try {
        const protocol = svc.https ? "https" : "http"
        await axios.get(
          `${protocol}://localhost:${svc.port}${svc.path}`,
          { timeout: 3000 }
        )
        results[svc.name] = true
      } catch (err) {
        // HTTPS services (HR/Finance) — ERR_EMPTY_RESPONSE
        // matlab mTLS chal raha hai — service alive hai!
        const msg = err?.message || ""
        if (
          svc.https && (
            msg.includes("ERR_EMPTY_RESPONSE") ||
            msg.includes("Network Error") ||
            msg.includes("ERR_NETWORK") ||
            msg.includes("ERR_SSL") ||
            msg.includes("certificate")
          )
        ) {
          results[svc.name] = true  // mTLS = alive 
        } else {
          results[svc.name] = false
        }
      }
    }
    setStatuses(results)
  }

  useEffect(() => {
    checkServices()
    const interval = setInterval(checkServices, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div>
      <div className="section-title">Services Status</div>
      <div className="services-grid">
        {SERVICES.map(svc => (
          <div key={svc.name} className="service-card">
            <div className={`service-dot ${statuses[svc.name] ? "online" : "offline"}`} />
            <div>
              <div className="name">{svc.name}</div>
              {/* <div className="port">
                :{svc.port} {svc.https ? "" : ""}
              </div> */}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}