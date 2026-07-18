import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Job } from "../types";

export default function MissingEmails() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.missingEmails.list().then((d: any) => {
      setJobs(d.jobs || []);
      setTotalCount(d.total_count || 0);
      setLoading(false);
    });
  }, []);

  return (
    <>
      <div className="page-header">
        <h2>Missing Emails <span className="count">({totalCount})</span></h2>
      </div>

      {loading && <div className="empty-guidance"><h3>Loading...</h3></div>}

      {!loading && jobs.length === 0 && (
        <div className="empty-guidance">
          <div className="empty-icon">&#10003;</div>
          <h3>All caught up</h3>
          <p>No matched jobs are missing an apply email.</p>
        </div>
      )}

      {!loading && jobs.length > 0 && (
        <div className="job-list">
          {jobs.map((job) => (
            <div key={job.id} className="job-card fade-in">
              <div className="job-card-header">
                <span className={"score-badge " + (job.match_score >= 50 ? "high" : job.match_score >= 30 ? "med" : "low")}>
                  {job.match_score}%
                </span>
                <div>
                  <Link to={`/jobs/${job.id}`} className="job-title">{job.title}</Link>
                  <div className="job-meta">{job.company} · {job.location} · {job.source}</div>
                </div>
                <span className="status-pill matched">matched</span>
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
                <span className="missing-email-note">No apply email found</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
