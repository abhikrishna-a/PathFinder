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

  return (
    <>
      <div className="page-header">
        <h2>Company Statistics</h2>
      </div>

      {loading && <div className="empty-guidance"><h3>Loading...</h3></div>}

      {!loading && companies.length === 0 && (
        <div className="empty-guidance">
          <div className="empty-icon">&#128202;</div>
          <h3>No company data</h3>
          <p>Company statistics will appear once jobs are fetched.</p>
        </div>
      )}

      {!loading && companies.length > 0 && (
        <div className="card card-dashboard">
          <table className="table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Jobs</th>
                <th>Avg Score</th>
                <th>Applied</th>
                <th>Top Skills</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((c) => (
                <tr key={c.company}>
                  <td><strong>{c.company}</strong></td>
                  <td>{c.job_count}</td>
                  <td>
                    <span className={"score-badge " + (c.avg_score >= 50 ? "high" : c.avg_score >= 30 ? "med" : "low")}>
                      {c.avg_score}%
                    </span>
                  </td>
                  <td>{c.applied_count}</td>
                  <td>
                    {c.skills.length > 0 ? (
                      <div className="job-skills">
                        {c.skills.map((s) => (
                          <span key={s} className="skill-tag">{s}</span>
                        ))}
                      </div>
                    ) : (
                      <span>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
