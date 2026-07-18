import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Chart, registerables } from "chart.js";
import { api } from "../api/client";

Chart.register(...registerables);

interface OverviewData {
  total_jobs: number;
  total_matched: number;
  total_applied: number;
  total_failed: number;
  total_ignored: number;
  total_web_apply: number;
  recent_jobs: { id: number; title: string; company: string; location: string; match_score: number; status: string; fetched_date: string }[];
  recent_apps: { id: number; job__id: number; job__title: string; job__company: string; job__match_score: number; status: string; sent_at: string }[];
  chart: { dates: string[]; fetched: number[]; matched: number[]; applied: number[] };
  top_skills: { skill_name: string; count: number }[];
}

function BriefcaseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
      <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
    </svg>
  );
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}

function SendIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function XCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="15" y1="9" x2="9" y2="15" />
      <line x1="9" y1="9" x2="15" y2="15" />
    </svg>
  );
}

function GlobeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10" />
      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
  );
}

export default function Overview() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetcherRunning, setFetcherRunning] = useState(false);
  const [fetcherStatus, setFetcherStatus] = useState("");
  const timelineRef = useRef<HTMLCanvasElement>(null);
  const skillsRef = useRef<HTMLCanvasElement>(null);
  const timelineChartRef = useRef<Chart | null>(null);
  const skillsChartRef = useRef<Chart | null>(null);

  useEffect(() => {
    api.stats.overview().then((d) => {
      setData(d as unknown as OverviewData);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!data || loading) return;

    if (timelineRef.current) {
      if (timelineChartRef.current) timelineChartRef.current.destroy();
      timelineChartRef.current = new Chart(timelineRef.current, {
        type: "line",
        data: {
          labels: data.chart.dates,
          datasets: [
            {
              label: "Fetched",
              data: data.chart.fetched,
              borderColor: "#2563EB",
              backgroundColor: "rgba(37,99,235,.08)",
              fill: true,
              tension: 0.4,
              pointRadius: 3,
              pointHoverRadius: 6,
              borderWidth: 2,
            },
            {
              label: "Matched",
              data: data.chart.matched,
              borderColor: "#16A34A",
              backgroundColor: "rgba(22,163,74,.08)",
              fill: true,
              tension: 0.4,
              pointRadius: 3,
              pointHoverRadius: 6,
              borderWidth: 2,
            },
            {
              label: "Applied",
              data: data.chart.applied,
              borderColor: "#D97706",
              backgroundColor: "rgba(217,119,6,.08)",
              fill: true,
              tension: 0.4,
              pointRadius: 3,
              pointHoverRadius: 6,
              borderWidth: 2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { intersect: false, mode: "index" },
          plugins: {
            legend: { position: "bottom", labels: { boxWidth: 12, padding: 16, color: "#64748B", font: { size: 12 } } },
          },
          scales: {
            x: { grid: { color: "#F1F5F9" }, ticks: { color: "#64748B", font: { size: 11 } } },
            y: { grid: { color: "#F1F5F9" }, ticks: { color: "#64748B", font: { size: 11 } } },
          },
        },
      });
    }

    if (skillsRef.current && data.top_skills.length > 0) {
      if (skillsChartRef.current) skillsChartRef.current.destroy();
      const colors = ["#2563EB", "#16A34A", "#D97706", "#7C3AED", "#0891B2", "#EA580C", "#EC4899", "#6366F1", "#14B8A6", "#DC2626"];
      skillsChartRef.current = new Chart(skillsRef.current, {
        type: "bar",
        data: {
          labels: data.top_skills.slice(0, 10).map((s) => s.skill_name),
          datasets: [{
            label: "Matches",
            data: data.top_skills.slice(0, 10).map((s) => s.count),
            backgroundColor: colors.slice(0, data.top_skills.length),
            borderRadius: 6,
            barThickness: 20,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: "y",
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: "#F1F5F9" }, ticks: { color: "#64748B", stepSize: 1, font: { size: 11 } } },
            y: { grid: { display: false }, ticks: { color: "#0F172A", font: { size: 12, weight: 500 } } },
          },
        },
      });
    }

    return () => {
      if (timelineChartRef.current) timelineChartRef.current.destroy();
      if (skillsChartRef.current) skillsChartRef.current.destroy();
    };
  }, [data, loading]);

  function handleRunFetcher() {
    setFetcherRunning(true);
    setFetcherStatus("");
    api.fetcher.run()
      .then(() => {
        setFetcherStatus("Fetcher started — refresh in a few seconds to see results");
        setTimeout(() => {
          setFetcherStatus("");
          setFetcherRunning(false);
        }, 5000);
      })
      .catch(() => {
        setFetcherStatus("Error running fetcher");
        setFetcherRunning(false);
      });
  }

  if (loading) {
    return (
      <>
        <div className="page-header"><h2>Overview</h2></div>
        <div className="bento-grid">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bento-card" style={{ background: "var(--surface-2)", borderRadius: "var(--radius)" }}>
              <div style={{ height: "20px", width: "60%", background: "var(--border)", borderRadius: "4px", marginBottom: "12px" }} />
              <div style={{ height: "36px", width: "40%", background: "var(--border)", borderRadius: "4px" }} />
            </div>
          ))}
        </div>
      </>
    );
  }

  if (!data) return <div className="empty-guidance"><h3>No data available</h3></div>;

  const total = data.total_jobs || 1;
  const segments = [
    { key: "matched", label: "Matched", count: data.total_matched, pct: (data.total_matched / total) * 100 },
    { key: "applied", label: "Applied", count: data.total_applied, pct: (data.total_applied / total) * 100 },
    { key: "web_apply", label: "Web Apply", count: data.total_web_apply, pct: (data.total_web_apply / total) * 100 },
    { key: "failed", label: "Failed", count: data.total_failed, pct: (data.total_failed / total) * 100 },
    { key: "ignored", label: "Ignored", count: data.total_ignored, pct: (data.total_ignored / total) * 100 },
  ];

  return (
    <>
      <div className="page-header">
        <h2>Overview</h2>
      </div>

      {/* Fetcher button */}
      <div className="fetcher-bar">
        <button className="btn-fetcher" onClick={handleRunFetcher} disabled={fetcherRunning}>
          {fetcherRunning ? (
            <span className="btn-fetcher-loading"><span className="spinner" /> Running...</span>
          ) : (
            <><RefreshIcon /> Run Fetcher</>
          )}
        </button>
        {fetcherStatus && (
          <span className={"fetcher-status " + (fetcherStatus.includes("Error") ? "error" : "success")}>
            {fetcherStatus}
          </span>
        )}
      </div>

      {/* Bento stat grid */}
      <div className="bento-grid">
        <div className="bento-card bento-card-hero bento-card-accent">
          <BriefcaseIcon className="stat-icon" />
          <div className="stat-number">{data.total_jobs.toLocaleString()}</div>
          <div className="stat-label">Total Jobs</div>
        </div>
        <div className="bento-card bento-card-sm bento-card-matched">
          <CheckCircleIcon className="stat-icon" />
          <div className="stat-number">{data.total_matched}</div>
          <div className="stat-label">Matched</div>
        </div>
        <div className="bento-card bento-card-sm bento-card-applied">
          <SendIcon className="stat-icon" />
          <div className="stat-number">{data.total_applied}</div>
          <div className="stat-label">Applied</div>
        </div>
        <div className="bento-card bento-card-sm bento-card-failed">
          <XCircleIcon className="stat-icon" />
          <div className="stat-number">{data.total_failed}</div>
          <div className="stat-label">Failed</div>
        </div>
        <div className="bento-card bento-card-sm bento-card-web">
          <GlobeIcon className="stat-icon" />
          <div className="stat-number">{data.total_web_apply}</div>
          <div className="stat-label">Web Apply</div>
        </div>
      </div>

      {/* Charts row */}
      <div className="charts-row">
        <div className="chart-container">
          <h3>Jobs Over Time</h3>
          <div style={{ height: "280px" }}>
            <canvas ref={timelineRef} />
          </div>
        </div>
        <div className="chart-container">
          <h3>Top Matched Skills</h3>
          <div style={{ height: "280px" }}>
            <canvas ref={skillsRef} />
          </div>
        </div>
      </div>

      {/* Status distribution */}
      <div className="status-dist">
        <h3>Jobs by Status</h3>
        <div className="status-bars">
          {segments.map((s) => (
            <div key={s.key} className="status-bar-row">
              <span className="status-bar-label">{s.label}</span>
              <div className="status-bar-wrap">
                <div className={"status-bar-fill " + s.key} style={{ width: `${Math.max(s.pct, 1)}%` }} />
              </div>
              <span className="status-bar-count">{s.count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Two-column: Recent Jobs + Applications */}
      <div className="two-col">
        <div className="panel">
          <h3>
            <Link to="/jobs" style={{ color: "var(--accent)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "6px" }}>
              Recent Matched Jobs <ArrowIcon />
            </Link>
          </h3>
          {data.recent_jobs.length === 0 ? (
            <p style={{ color: "var(--muted)", fontSize: "14px" }}>No jobs yet. Run the fetcher to get started.</p>
          ) : (
            <>
              {data.recent_jobs.slice(0, 5).map((j) => (
                <div key={j.id} className="list-item">
                  <div className="item-header">
                    <span className={"score-badge " + (j.match_score >= 50 ? "high" : j.match_score >= 30 ? "med" : "low")}>{j.match_score}%</span>
                    <Link to={`/jobs/${j.id}`}>{j.title}</Link>
                  </div>
                  <div className="item-sub">{j.company} · {j.location} · {j.status}</div>
                </div>
              ))}
              <div className="panel-footer">
                <Link to="/jobs?status=matched">View All Matched Jobs →</Link>
              </div>
            </>
          )}
        </div>

        <div className="panel">
          <h3>
            <Link to="/applications" style={{ color: "var(--accent)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "6px" }}>
              Recent Applications <ArrowIcon />
            </Link>
          </h3>
          {data.recent_apps.length === 0 ? (
            <p style={{ color: "var(--muted)", fontSize: "14px" }}>No applications sent yet.</p>
          ) : (
            <>
              {data.recent_apps.slice(0, 5).map((a) => (
                <div key={a.id} className="list-item">
                  <div className="item-header">
                    <span className={"status-badge " + a.status}>{a.status}</span>
                    <Link to={`/jobs/${a.job__id}`}>{a.job__title}</Link>
                  </div>
                  <div className="item-sub">{a.job__company} · {new Date(a.sent_at).toLocaleDateString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</div>
                </div>
              ))}
              <div className="panel-footer">
                <Link to="/applications">View All Applications →</Link>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Top Skills */}
      {data.top_skills.length > 0 && (
        <div className="panel">
          <h3>
            <Link to="/stats/skills" style={{ color: "var(--accent)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "6px" }}>
              Top Skills <ArrowIcon />
            </Link>
          </h3>
          <div className="job-skills" style={{ gap: "6px" }}>
            {data.top_skills.map((s) => (
              <span key={s.skill_name} className="skill-tag" title={`${s.count} occurrences`}>
                {s.skill_name} <small>({s.count})</small>
              </span>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
