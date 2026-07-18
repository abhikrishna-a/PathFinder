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

  if (loading) {
    return (
      <>
        <div className="page-header"><h2>Locations</h2></div>
        <div className="st-loading">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="pf-skeleton pf-skeleton-line" style={{ height: 36, width: `${80 - i * 10}%` }} />
          ))}
        </div>
      </>
    );
  }

  if (locations.length === 0) {
    return (
      <>
        <div className="page-header"><h2>Locations</h2></div>
        <div className="st-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
          <h3>No location data</h3>
          <p>Location statistics will appear once jobs are fetched.</p>
        </div>
      </>
    );
  }

  const top = locations[0];
  const topPct = top ? top.pct : 0;

  return (
    <>
      <div className="page-header">
        <h2>Locations <span className="count">({total} jobs)</span></h2>
      </div>

      {/* Summary cards */}
      <div className="st-summary-row">
        <div className="st-summary-card">
          <span className="st-summary-value">{locations.length}</span>
          <span className="st-summary-label">Regions</span>
        </div>
        <div className="st-summary-card">
          <span className="st-summary-value">{top?.location || "—"}</span>
          <span className="st-summary-label">Top Region</span>
        </div>
        <div className="st-summary-card">
          <span className="st-summary-value">{topPct}%</span>
          <span className="st-summary-label">Top Region Share</span>
        </div>
      </div>

      {/* Bar chart */}
      <div className="st-card">
        <h3 className="st-card-title">Job Distribution by Location</h3>
        <div className="st-bars">
          {locations.map((l) => (
            <div key={l.location} className="st-bar-row">
              <span className="st-bar-label">{l.location || "Unknown"}</span>
              <div className="st-bar-track">
                <div className="st-bar-fill" style={{ width: `${Math.max(l.pct, 1)}%` }} />
              </div>
              <span className="st-bar-value">{l.count}</span>
              <span className="st-bar-pct">{l.pct}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="st-card">
        <h3 className="st-card-title">All Locations</h3>
        <table className="st-table">
          <thead>
            <tr>
              <th>Location</th>
              <th className="st-col-right">Jobs</th>
              <th className="st-col-right">Share</th>
              <th className="st-col-right">Distribution</th>
            </tr>
          </thead>
          <tbody>
            {locations.map((l) => (
              <tr key={l.location}>
                <td className="st-cell-name">{l.location || "Unknown"}</td>
                <td className="st-cell-right st-cell-num">{l.count}</td>
                <td className="st-cell-right st-cell-num">{l.pct}%</td>
                <td className="st-cell-right">
                  <div className="st-table-bar">
                    <div className="st-table-bar-fill" style={{ width: `${Math.max(l.pct, 1)}%` }} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
