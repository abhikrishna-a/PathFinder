import { useEffect, useState } from "react";
import { api } from "../api/client";

interface SkillRow {
  skill_name: string;
  total: number;
  found_count: number;
  highlighted_count: number;
  pct: number;
}

interface ComboRow {
  skills: string[];
  count: number;
}

export default function SkillStats() {
  const [skills, setSkills] = useState<SkillRow[]>([]);
  const [combos, setCombos] = useState<ComboRow[]>([]);
  const [totalApps, setTotalApps] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.stats.skills().then((d: any) => {
      setSkills(d.skills || []);
      setCombos(d.top_combos || []);
      setTotalApps(d.total_apps || 0);
      setLoading(false);
    });
  }, []);

  return (
    <>
      <div className="page-header">
        <h2>Skill Statistics <span className="count">({totalApps} applications)</span></h2>
      </div>

      {loading && <div className="empty-guidance"><h3>Loading...</h3></div>}

      {!loading && (
        <>
          {/* Horizontal bar chart */}
          {skills.length > 0 && (
            <div className="card card-dashboard" style={{ marginBottom: "1.5rem", padding: "1.5rem" }}>
              <h3 style={{ marginBottom: "1rem" }}>Skill Frequency</h3>
              {skills.slice(0, 12).map((s) => (
                <div key={s.skill_name} style={{ display: "flex", alignItems: "center", marginBottom: "0.5rem" }}>
                  <span style={{ width: "140px", fontSize: "0.85rem", textAlign: "right", paddingRight: "12px", flexShrink: 0 }}>
                    {s.skill_name}
                  </span>
                  <div style={{ flex: 1, background: "var(--bg-secondary, #1a1a2e)", borderRadius: "4px", height: "22px", overflow: "hidden" }}>
                    <div style={{
                      width: `${s.pct}%`,
                      height: "100%",
                      background: "linear-gradient(90deg, var(--accent, #6c63ff), var(--accent-hover, #8b83ff))",
                      borderRadius: "4px",
                      transition: "width 0.6s ease",
                    }} />
                  </div>
                  <span style={{ width: "60px", fontSize: "0.8rem", paddingLeft: "8px", flexShrink: 0 }}>
                    {s.pct}% ({s.total})
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Skills table */}
          {skills.length > 0 && (
            <div className="card card-dashboard" style={{ marginBottom: "1.5rem" }}>
              <h3 style={{ padding: "1rem 1.5rem 0" }}>All Skills</h3>
              <table className="table">
                <thead>
                  <tr>
                    <th>Skill</th>
                    <th>Total</th>
                    <th>In Job Desc</th>
                    <th>Highlighted</th>
                    <th>% of Apps</th>
                  </tr>
                </thead>
                <tbody>
                  {skills.map((s) => (
                    <tr key={s.skill_name}>
                      <td>{s.skill_name}</td>
                      <td>{s.total}</td>
                      <td>{s.found_count}</td>
                      <td>{s.highlighted_count}</td>
                      <td>{s.pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Skill combos */}
          {combos.length > 0 && (
            <div className="card card-dashboard">
              <h3 style={{ padding: "1rem 1.5rem 0" }}>Top Skill Combos</h3>
              <table className="table">
                <thead>
                  <tr>
                    <th>Skill Pair</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {combos.map((c, i) => (
                    <tr key={i}>
                      <td>{c.skills.join(" + ")}</td>
                      <td>{c.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </>
  );
}
