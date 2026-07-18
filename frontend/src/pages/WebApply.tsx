import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

interface WebApplyItem {
  id: number;
  job_title?: string;
  company_name?: string;
  applied_on?: string;
  sent_at?: string;
  application_method?: string;
  status?: string;
  job?: { id: number; title: string; company?: string; company_name?: string };
}

export default function WebApply() {
  const [items, setItems] = useState<WebApplyItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.webApply.list().then((d: any) => {
      setItems(d.applications || []);
      setTotalCount(d.total_count || 0);
      setLoading(false);
    });
  }, []);

  return (
    <>
      <div className="page-header">
        <h2>Web Apply <span className="count">({totalCount})</span></h2>
      </div>

      {loading && <div className="empty-guidance"><h3>Loading...</h3></div>}

      {!loading && items.length === 0 && (
        <div className="empty-guidance">
          <div className="empty-icon">&#9993;</div>
          <h3>No web applications found</h3>
          <p>Jobs applied via the browser will appear here.</p>
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="app-list">
          {items.map((app) => (
            <div key={app.id} className={"app-card status-" + (app.status || "web_apply")}>
              <div className="app-header">
                <span className="status-badge web_apply">web apply</span>
                <div>
                  {app.job ? (
                    <Link to={`/jobs/${app.job.id}`} className="job-title">
                      {app.job.title}
                    </Link>
                  ) : (
                    <span className="job-title">{app.job_title || "Unknown Job"}</span>
                  )}
                  <div className="job-meta">
                    {app.company_name || app.job?.company || app.job?.company_name || "—"}
                    {app.application_method && <> · {app.application_method}</>}
                  </div>
                </div>
                <div className="app-date">
                  {app.sent_at
                    ? new Date(app.sent_at).toLocaleDateString("en-IN", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : app.applied_on || "—"}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
