import { useEffect, useState } from "react";
import { api } from "../api/client";

interface CompanyRow {
  company: string;
  job_count: number;
  avg_score: number;
  applied_count: number;
  skills: string[];
}

export default function CompanyStats() {
  const [companies, setCompanies] = useState<CompanyRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.stats.companies().then((d: any) => {
      setCompanies(d.companies || []);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <>
        <div className="page-header"><h2>Companies</h2></div>
        <div className="st-loading">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="pf-skeleton pf-skeleton-line" style={{ height: 80, width: "100%" }} />
          ))}
        </div>
      </>
    );
  }

  if (companies.length === 0) {
    return (
      <>
        <div className="page-header"><h2>Companies</h2></div>
        <div className="st-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
            <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
          </svg>
          <h3>No company data</h3>
          <p>Company statistics will appear once jobs are fetched.</p>
        </div>
      </>
    );
  }

  const totalJobs = companies.reduce((sum, c) => sum + c.job_count, 0);
  const totalApplied = companies.reduce((sum, c) => sum + c.applied_count, 0);
  const topCompany = companies[0];

  return (
    <>
      <div className="page-header">
        <h2>Companies <span className="count">({companies.length})</span></h2>
      </div>

      {/* Summary */}
      <div className="st-summary-row">
        <div className="st-summary-card">
          <span className="st-summary-value">{companies.length}</span>
          <span className="st-summary-label">Companies</span>
        </div>
        <div className="st-summary-card">
          <span className="st-summary-value">{totalJobs}</span>
          <span className="st-summary-label">Total Jobs</span>
        </div>
        <div className="st-summary-card">
          <span className="st-summary-value">{totalApplied}</span>
          <span className="st-summary-label">Applications</span>
        </div>
        <div className="st-summary-card">
          <span className="st-summary-value">{topCompany?.company || "—"}</span>
          <span className="st-summary-label">Most Jobs</span>
        </div>
      </div>

      {/* Company cards grid */}
      <div className="st-company-grid">
        {companies.map((c) => (
          <div key={c.company} className="st-company-card">
            <div className="st-company-head">
              <div className="st-company-icon">
                {c.company.charAt(0).toUpperCase()}
              </div>
              <div className="st-company-info">
                <span className="st-company-name">{c.company}</span>
                <span className="st-company-sub">
                  {c.job_count} job{c.job_count !== 1 ? "s" : ""}
                  {c.applied_count > 0 && ` · ${c.applied_count} applied`}
                </span>
              </div>
              <span className={"st-score " + (c.avg_score >= 50 ? "high" : c.avg_score >= 30 ? "med" : "low")}>
                {c.avg_score}%
              </span>
            </div>
            {c.skills.length > 0 && (
              <div className="st-company-skills">
                {c.skills.map((s) => (
                  <span key={s} className="skill-tag">{s}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
