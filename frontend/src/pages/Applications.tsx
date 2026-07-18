import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Application, PaginatedResponse } from "../types";

const STATUSES = ["all", "sent", "failed"];

export default function Applications() {
  const [status, setStatus] = useState("all");
  const [data, setData] = useState<PaginatedResponse<Application> | null>(null);
  const [loading, setLoading] = useState(true);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (status !== "all") params.status = status;
    api.applications.list(params).then((d) => {
      setData(d);
      setLoading(false);
    });
  }, [status]);

  return (
    <>
      <div className="page-header">
        <h2>Applications <span className="count">({data?.count ?? "..."})</span></h2>
      </div>

      <div className="filter-bar">
        <div className="filter-row">
          <div className="filter-pill">
            <button className={"filter-pill-btn" + (status !== "all" ? " has-value" : "")}
              onClick={() => setOpenDropdown(openDropdown === "status" ? null : "status")}>
              {status === "all" ? "Status" : status.charAt(0).toUpperCase() + status.slice(1)}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
            </button>
            <div className={"dropdown-menu" + (openDropdown === "status" ? " open" : "")}>
              {STATUSES.map((s) => (
                <button key={s} className={"dropdown-item" + (status === s ? " active" : "")}
                  onClick={() => { setStatus(s); setOpenDropdown(null); }}>
                  <svg className="dropdown-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                  {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>
          </div>
          {status !== "all" && (
            <button className="filter-clear visible" onClick={() => { setStatus("all"); setOpenDropdown(null); }}>Clear all</button>
          )}
          <span className="filter-result-count" style={{ marginLeft: "auto" }}>{data?.count ?? 0} results</span>
        </div>
      </div>

      <div className="app-list">
        {loading && <div className="empty-guidance"><h3>Loading...</h3></div>}
        {!loading && data?.results.map((app) => (
          <div key={app.id} className={"app-card status-" + app.status}>
            <div className="app-header">
              <span className={"status-badge " + (app.status === "sent" ? "sent" : "failed")}>{app.status}</span>
              <div>
                <Link to={`/jobs/${app.job.id}`} className="job-title">{app.job.title}</Link>
                <div className="job-meta">{app.job.company} &middot; Score: {app.job.match_score}%</div>
              </div>
              <div className="app-date">{new Date(app.sent_at).toLocaleDateString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</div>
            </div>
            {app.skills_highlighted?.length > 0 && (
              <div className="app-skills">
                <label>Skills matched:</label>
                {app.skills_highlighted.map((s) => <span key={s} className="skill-tag">{s}</span>)}
                <span className="match-pct">{app.skill_match_pct}% match</span>
              </div>
            )}
          </div>
        ))}
        {!loading && data?.results.length === 0 && (
          <div className="empty-guidance">
            <div className="empty-icon">&#9993;</div>
            <h3>No applications found</h3>
            <p>No applications match the current filter.</p>
          </div>
        )}
      </div>

      {openDropdown && (
        <div style={{ position: "fixed", inset: 0, zIndex: 99 }} onClick={() => setOpenDropdown(null)} />
      )}
    </>
  );
}
