import { useEffect, useState } from "react";
import { api } from "../api/client";

interface LocationRow {
  location: string;
  count: number;
  pct: number;
}

export default function LocationStats() {
  const [locations, setLocations] = useState<LocationRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.stats.locations().then((d: any) => {
      setLocations(d.locations || []);
      setTotal(d.total || 0);
      setLoading(false);
    });
  }, []);

  return (
    <>
      <div className="page-header">
        <h2>Location Statistics <span className="count">({total} jobs)</span></h2>
      </div>

      {loading && <div className="empty-guidance"><h3>Loading...</h3></div>}

      {!loading && locations.length === 0 && (
        <div className="empty-guidance">
          <div className="empty-icon">&#127758;</div>
          <h3>No location data</h3>
          <p>Location statistics will appear once jobs are fetched.</p>
        </div>
      )}

      {!loading && locations.length > 0 && (
        <>
          {/* Horizontal bar chart */}
          <div className="card card-dashboard" style={{ marginBottom: "1.5rem", padding: "1.5rem" }}>
            <h3 style={{ marginBottom: "1rem" }}>Job Distribution by Location</h3>
            {locations.map((l) => (
              <div key={l.location} style={{ display: "flex", alignItems: "center", marginBottom: "0.5rem" }}>
                <span style={{ width: "140px", fontSize: "0.85rem", textAlign: "right", paddingRight: "12px", flexShrink: 0 }}>
                  {l.location || "Unknown"}
                </span>
                <div style={{ flex: 1, background: "var(--bg-secondary, #1a1a2e)", borderRadius: "4px", height: "22px", overflow: "hidden" }}>
                  <div style={{
                    width: `${l.pct}%`,
                    height: "100%",
                    background: "linear-gradient(90deg, var(--accent, #6c63ff), var(--accent-hover, #8b83ff))",
                    borderRadius: "4px",
                    transition: "width 0.6s ease",
                  }} />
                </div>
                <span style={{ width: "80px", fontSize: "0.8rem", paddingLeft: "8px", flexShrink: 0 }}>
                  {l.count} ({l.pct}%)
                </span>
              </div>
            ))}
          </div>

          {/* Table */}
          <div className="card card-dashboard">
            <table className="table">
              <thead>
                <tr>
                  <th>Location</th>
                  <th>Count</th>
                  <th>%</th>
                </tr>
              </thead>
              <tbody>
                {locations.map((l) => (
                  <tr key={l.location}>
                    <td>{l.location || "Unknown"}</td>
                    <td>{l.count}</td>
                    <td>{l.pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}
