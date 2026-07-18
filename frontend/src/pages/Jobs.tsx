import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { api } from "../api/client";
import type { Job, PaginatedResponse } from "../types";

const STATUSES = ["all", "new", "matched", "applied", "web_apply", "ignored"];
const LOCATIONS = ["all", "kerala", "india", "remote"];
const SALARIES = [
  { value: "all", label: "All" },
  { value: "has", label: "Has Salary" },
  { value: "3l", label: "₹3L+ PA" },
  { value: "6l", label: "₹6L+ PA" },
  { value: "10l", label: "₹10L+ PA" },
];
const SORT_OPTIONS = [
  { value: "-match_score", label: "Score (High to Low)" },
  { value: "match_score", label: "Score (Low to High)" },
  { value: "-fetched_date", label: "Date (Newest First)" },
  { value: "company", label: "Company (A → Z)" },
  { value: "title", label: "Title (A → Z)" },
  { value: "-salary", label: "Salary (High to Low)" },
  { value: "salary", label: "Salary (Low to High)" },
];

function statusBadge(label: string) {
  return label === "all" ? "Status" : label.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function salaryLabel(value: string) {
  const f = SALARIES.find((s) => s.value === value);
  return f ? f.label : "Salary";
}

export default function Jobs() {
  const [searchParams, setSearchParams] = useSearchParams();
  const status = searchParams.get("status") || "all";
  const location = searchParams.get("location") || "all";
  const salary = searchParams.get("salary") || "all";
  const sort = searchParams.get("sort") || "-match_score";
  const page = searchParams.get("page") || "1";
  const [searchQuery, setSearchQuery] = useState("");

  const [data, setData] = useState<PaginatedResponse<Job> | null>(null);
  const [loading, setLoading] = useState(true);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api.jobs.list({ status, location, salary, sort, page, search: searchQuery }).then((d) => {
      setData(d);
      setLoading(false);
    });
  }, [status, location, salary, sort, page]);

  function setParam(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    next.set(key, value);
    if (key !== "page") next.set("page", "1");
    setSearchParams(next);
    setOpenDropdown(null);
  }

  function clearAll() {
    setSearchParams({});
    setOpenDropdown(null);
  }

  const hasFilters = status !== "all" || location !== "all" || salary !== "all";

  const sortLabel = SORT_OPTIONS.find((s) => s.value === sort)?.label || "Sort";

  return (
    <>
      <div className="page-header">
        <h2>All Jobs <span className="count">({data?.count ?? "..."})</span></h2>
      </div>

      <div className="filter-bar">
        <div className="search-box">
          <svg className="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg>
          <input type="text" placeholder="Search by title, company, or skill..." value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") setParam("search", searchQuery); }} />
        </div>

        <div className="filter-row">
          {/* Status */}
          <div className="filter-pill">
            <button className={"filter-pill-btn" + (status !== "all" ? " has-value" : "")}
              onClick={() => setOpenDropdown(openDropdown === "status" ? null : "status")}>
              {statusBadge(status)}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
            </button>
            <div className={"dropdown-menu" + (openDropdown === "status" ? " open" : "")}>
              {STATUSES.map((s) => (
                <button key={s} className={"dropdown-item" + (status === s ? " active" : "")}
                  onClick={() => setParam("status", s)}>
                  <svg className="dropdown-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                  {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1).replace("_", " ")}
                </button>
              ))}
            </div>
          </div>

          {/* Location */}
          <div className="filter-pill">
            <button className={"filter-pill-btn" + (location !== "all" ? " has-value" : "")}
              onClick={() => setOpenDropdown(openDropdown === "location" ? null : "location")}>
              {location === "all" ? "Location" : location.charAt(0).toUpperCase() + location.slice(1)}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
            </button>
            <div className={"dropdown-menu" + (openDropdown === "location" ? " open" : "")}>
              {LOCATIONS.map((l) => (
                <button key={l} className={"dropdown-item" + (location === l ? " active" : "")}
                  onClick={() => setParam("location", l)}>
                  <svg className="dropdown-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                  {l === "all" ? "All" : l.charAt(0).toUpperCase() + l.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Salary */}
          <div className="filter-pill">
            <button className={"filter-pill-btn" + (salary !== "all" ? " has-value" : "")}
              onClick={() => setOpenDropdown(openDropdown === "salary" ? null : "salary")}>
              {salaryLabel(salary)}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
            </button>
            <div className={"dropdown-menu" + (openDropdown === "salary" ? " open" : "")}>
              {SALARIES.map((s) => (
                <button key={s.value} className={"dropdown-item" + (salary === s.value ? " active" : "")}
                  onClick={() => setParam("salary", s.value)}>
                  <svg className="dropdown-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Clear */}
          <button className={"filter-clear" + (hasFilters ? " visible" : "")} onClick={clearAll}>Clear all</button>

          {/* Sort */}
          <div className="filter-pill" style={{ marginLeft: "auto" }}>
            <button className="filter-pill-btn"
              onClick={() => setOpenDropdown(openDropdown === "sort" ? null : "sort")}>
              {sortLabel}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
            </button>
            <div className={"dropdown-menu dropdown-menu-right" + (openDropdown === "sort" ? " open" : "")}>
              {SORT_OPTIONS.map((s) => (
                <button key={s.value} className={"dropdown-item" + (sort === s.value ? " active" : "")}
                  onClick={() => setParam("sort", s.value)}>
                  <svg className="dropdown-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <span className="filter-result-count">{data?.count ?? 0} results</span>
        </div>
      </div>

      {/* Job cards */}
      <div className="job-list">
        {loading && <div className="empty-guidance"><h3>Loading...</h3></div>}
        {!loading && data?.results.length === 0 && (
          <div className="empty-guidance">
            <div className="empty-icon">🔍</div>
            <h3>No jobs found</h3>
            <p>Try adjusting your filters or search query.</p>
          </div>
        )}
        {!loading && data?.results.map((job) => (
          <div key={job.id} className="job-card fade-in" data-title={job.title.toLowerCase()} data-company={job.company.toLowerCase()}>
            <div className="job-card-header">
              <span className={"score-badge " + (job.match_score >= 50 ? "high" : job.match_score >= 30 ? "med" : "low")}>
                {job.match_score}%
              </span>
              <div>
                <Link to={`/jobs/${job.id}`} className="job-title">{job.title}</Link>
                <div className="job-meta">{job.company} &middot; {job.location} &middot; {job.source}</div>
              </div>
              <span className={"status-pill " + job.status}>{job.status.replace("_", " ")}</span>
            </div>
            {job.matched_skills?.length > 0 && (
              <div className="job-skills">
                {job.matched_skills.map((skill) => (
                  <span key={skill} className="skill-tag">{skill}</span>
                ))}
              </div>
            )}
            <div className="job-footer">
              <span>Posted: {job.posted_date || "N/A"}</span>
              {job.salary_display && <span className="job-salary">{job.salary_display}</span>}
              <span>Fetched: {new Date(job.fetched_date).toLocaleDateString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="pagination">
          {data.previous && (
            <button className="btn" onClick={() => setParam("page", String(Number(page) - 1))}>&laquo; Previous</button>
          )}
          <span className="page-info">Page {data.page} of {data.total_pages}</span>
          {data.next && (
            <button className="btn" onClick={() => setParam("page", String(Number(page) + 1))}>Next &raquo;</button>
          )}
        </div>
      )}

      {/* Click-outside close */}
      {openDropdown && (
        <div style={{ position: "fixed", inset: 0, zIndex: 99 }} onClick={() => setOpenDropdown(null)} />
      )}
    </>
  );
}
