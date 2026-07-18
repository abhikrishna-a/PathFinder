import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import Markdown from "react-markdown";
import { api } from "../api/client";
import type { JobDetail as JobDetailType } from "../types";

export default function JobDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState<JobDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDesc, setShowDesc] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeSkillTab, setActiveSkillTab] = useState<"matched" | "gaps" | "analysis">("matched");

  useEffect(() => {
    if (!id) return;
    api.jobs.detail(Number(id)).then((d) => {
      setJob(d);
      setLoading(false);
    });
  }, [id]);

  function copyCoverLetter() {
    if (!job?.application?.cover_letter_text) return;
    navigator.clipboard.writeText(job.application.cover_letter_text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  if (loading) return <div className="empty-guidance"><h3>Loading...</h3></div>;
  if (!job) return <div className="empty-guidance"><h3>Job not found</h3></div>;

  const app = job.application;
  const maxWeight = job.skill_score_breakdown
    ? Math.max(...Object.values(job.skill_score_breakdown), 1)
    : 1;

  return (
    <>
      <div className="detail-header">
        <Link to="/jobs" className="back-link">← Back to Jobs</Link>
        <h2>{job.title}</h2>
        <div className="detail-meta">
          <span className={"score-badge " + (job.match_score >= 50 ? "high" : job.match_score >= 30 ? "med" : "low")}>
            {job.match_score}%
          </span>
          <span>{job.company}</span> ·
          <span>{job.location}</span> ·
          <span>{job.source}</span> ·
          {job.salary_display && <><span className="job-salary">{job.salary_display}</span> ·</>}
          <span className={"status-pill " + job.status}>{job.status}</span>
        </div>
      </div>

      {job.filter_reason && (
        <div className="filter-reason-banner">
          Filtered: {job.filter_reason}
        </div>
      )}

      <div className="two-col">
        {/* ── Left: Job Details ────────────────────────────── */}
        <div className="panel">
          <h3>Job Details</h3>

          <div className="detail-grid">
            <div className="detail-section">
              <label>Posted</label>
              <div>{job.posted_date || "N/A"}</div>
            </div>
            <div className="detail-section">
              <label>Fetched</label>
              <div>{job.fetched_date ? new Date(job.fetched_date).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "N/A"}</div>
            </div>
            {job.salary_display && (
              <div className="detail-section">
                <label>Salary</label>
                <div>
                  <span className="job-salary">{job.salary_display}</span>
                  {job.salary ? <span style={{ marginLeft: "8px", fontSize: "13px", color: "var(--muted)" }}>₹{job.salary.toLocaleString("en-IN")}/yr</span> : null}
                </div>
              </div>
            )}
            {job.search_query && (
              <div className="detail-section">
                <label>Search Query</label>
                <div className="search-query-tag">{job.search_query}</div>
              </div>
            )}
            {job.apply_email && (
              <div className="detail-section">
                <label>Apply Email</label>
                <div>{job.apply_email}</div>
              </div>
            )}
            {job.apply_url && (
              <div className="detail-section full-width">
                <label>Apply URL</label>
                <div><a href={job.apply_url} target="_blank" rel="noopener noreferrer" className="detail-link">{job.apply_url.length > 60 ? job.apply_url.slice(0, 60) + "…" : job.apply_url}</a></div>
              </div>
            )}
          </div>

          {/* Description — collapsible */}
          {job.description && (
            <div className="detail-section" style={{ marginTop: "16px" }}>
              <label>Description</label>
              <div className={"job-description-box" + (showDesc ? " expanded" : "")}>
                <div className="job-description-content">
                  <Markdown>{showDesc ? job.description : job.description.slice(0, 300) + (job.description.length > 300 ? "…" : "")}</Markdown>
                </div>
                {job.description.length > 300 && (
                  <button type="button" className="desc-toggle" onClick={() => setShowDesc(!showDesc)}>
                    {showDesc ? "Show less" : "Show full description"}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* ── Right: Skills, Gaps, Analysis ────────────────── */}
        <div className="panel">
          {/* Tab bar */}
          <div className="skill-tabs">
            <button className={"skill-tab" + (activeSkillTab === "matched" ? " active" : "")} onClick={() => setActiveSkillTab("matched")}>
              Matched Skills
              {job.matched_skills?.length > 0 && <span className="skill-tab-count">{job.matched_skills.length}</span>}
            </button>
            <button className={"skill-tab" + (activeSkillTab === "gaps" ? " active" : "")} onClick={() => setActiveSkillTab("gaps")}>
              Skill Gaps
              {job.skill_gaps?.length > 0 && <span className="skill-tab-count gap">{job.skill_gaps.length}</span>}
            </button>
            <button className={"skill-tab" + (activeSkillTab === "analysis" ? " active" : "")} onClick={() => setActiveSkillTab("analysis")}>
              Analysis
            </button>
          </div>

          {/* ── Matched Skills Tab ──────────────────────────── */}
          {activeSkillTab === "matched" && (
            <div className="skill-tab-content">
              {job.matched_skills?.length > 0 ? (
                <div className="skill-bars">
                  {job.matched_skills.map((skill) => {
                    const weight = job.skill_score_breakdown?.[skill] ?? 0;
                    const pct = maxWeight > 0 ? (weight / maxWeight) * 100 : 0;
                    return (
                      <div key={skill} className="skill-bar-row">
                        <div className="skill-bar-info">
                          <span className="skill-bar-name">{skill}</span>
                          {weight > 0 && <span className="skill-bar-pts">+{weight} pts</span>}
                        </div>
                        <div className="skill-bar-track">
                          <div className="skill-bar-fill" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p style={{ color: "var(--muted)", fontSize: "14px", padding: "20px 0" }}>No skills matched.</p>
              )}
            </div>
          )}

          {/* ── Skill Gaps Tab ──────────────────────────────── */}
          {activeSkillTab === "gaps" && (
            <div className="skill-tab-content">
              {job.skill_gaps?.length > 0 ? (
                <div className="gaps-list">
                  {job.skill_gaps.map((gap, i) => (
                    <div key={gap} className="gap-row">
                      <span className="gap-number">{i + 1}</span>
                      <span className="gap-name">{gap}</span>
                      <span className="gap-label">missing</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="gaps-empty">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                    <polyline points="22 4 12 14.01 9 11.01" />
                  </svg>
                  <p>No skill gaps — you match all required skills!</p>
                </div>
              )}
            </div>
          )}

          {/* ── Analysis Tab ────────────────────────────────── */}
          {activeSkillTab === "analysis" && (
            <div className="skill-tab-content">
              {job.match_explanation ? (
                <div className="analysis-box">
                  <div className="analysis-header">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="16" x2="12" y2="12" />
                      <line x1="12" y1="8" x2="12.01" y2="8" />
                    </svg>
                    <span>Match Analysis</span>
                  </div>
                  <p className="analysis-text">{job.match_explanation}</p>

                  {/* Skill score summary */}
                  {job.skill_score_breakdown && Object.keys(job.skill_score_breakdown).length > 0 && (
                    <div className="analysis-scores">
                      <div className="analysis-score-header">Score Breakdown</div>
                      <div className="analysis-score-grid">
                        {Object.entries(job.skill_score_breakdown)
                          .sort(([, a], [, b]) => b - a)
                          .map(([skill, pts]) => (
                            <div key={skill} className="analysis-score-item">
                              <span className="analysis-score-skill">{skill}</span>
                              <span className="analysis-score-pts">+{pts}</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p style={{ color: "var(--muted)", fontSize: "14px", padding: "20px 0" }}>No analysis available.</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Application Section (full width) ───────────────── */}
      {app && (
        <div className="panel" style={{ marginTop: "20px" }}>
          <h3>Application</h3>
          <div className="app-detail-grid">
            <div className="detail-section">
              <label>Status</label>
              <div><span className={"status-pill " + app.status}>{app.status}</span></div>
            </div>
            <div className="detail-section">
              <label>Sent</label>
              <div>{app.sent_at ? new Date(app.sent_at).toLocaleDateString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "N/A"}</div>
            </div>
            {app.email_subject && (
              <div className="detail-section full-width">
                <label>Email Subject</label>
                <div>{app.email_subject}</div>
              </div>
            )}
            {app.error_message && (
              <div className="detail-section full-width">
                <label>Error</label>
                <div className="error-text">{app.error_message}</div>
              </div>
            )}
          </div>

          {/* Criteria grid */}
          {app.criteria_data && Object.keys(app.criteria_data).length > 0 && (
            <>
              <h3 style={{ marginTop: "16px" }}>Criteria Sent</h3>
              <div className="criteria-grid">
                {app.criteria_data.role_level && (
                  <div className="criteria-item">
                    <span className="criteria-label">Role Level:</span>
                    <span className="criteria-value">{String(app.criteria_data.role_level)}</span>
                  </div>
                )}
                {app.criteria_data.min_years_required && (
                  <div className="criteria-item">
                    <span className="criteria-label">Exp Required:</span>
                    <span className="criteria-value">{String(app.criteria_data.min_years_required)}yr</span>
                  </div>
                )}
                {app.criteria_data.sections_included && (
                  <div className="criteria-item">
                    <span className="criteria-label">Sections:</span>
                    <span className="criteria-value">{String(app.criteria_data.sections_included)}</span>
                  </div>
                )}
                {app.criteria_data.project_mentioned && (
                  <div className="criteria-item">
                    <span className="criteria-label">Project:</span>
                    <span className="criteria-value">{String(app.criteria_data.project_mentioned)}</span>
                  </div>
                )}
                {app.criteria_data.email_used && (
                  <div className="criteria-item">
                    <span className="criteria-label">Email:</span>
                    <span className="criteria-value">{String(app.criteria_data.email_used)}</span>
                  </div>
                )}
                <div className="criteria-item">
                  <span className="criteria-label">Resume:</span>
                  <span className={"criteria-value" + (app.criteria_data.resume_attached ? " good" : " bad")}>
                    {app.criteria_data.resume_attached ? "Attached" : "Missing"}
                  </span>
                </div>
              </div>
            </>
          )}

          {app.skill_gaps?.length > 0 && (
            <div className="app-gaps" style={{ marginTop: "12px" }}>
              <label>Skill Gaps:</label>
              {app.skill_gaps.map((gap) => (
                <span key={gap} className="skill-tag gap">{gap}</span>
              ))}
            </div>
          )}

          {app.cover_letter_text && (
            <>
              <details className="cover-letter-section" style={{ marginTop: "16px" }}>
                <summary>View Cover Letter</summary>
                <pre className="cover-letter">{app.cover_letter_text}</pre>
              </details>
              <button type="button" className={"btn-copy" + (copied ? " copied" : "")} onClick={copyCoverLetter}>
                {copied ? "Copied!" : "Copy Cover Letter"}
              </button>
            </>
          )}
        </div>
      )}

      {/* ── Action buttons ─────────────────────────────────── */}
      <div style={{ display: "flex", gap: "12px", marginTop: "20px" }}>
        {job.apply_url && (
          <a href={job.apply_url} target="_blank" rel="noopener noreferrer" className="apply-link">
            Apply Now →
          </a>
        )}
        {job.job_url && (
          <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="apply-btn">
            View Original Job →
          </a>
        )}
        <button className="btn" onClick={() => navigate(-1)}>
          Go Back
        </button>
      </div>
    </>
  );
}
