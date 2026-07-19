import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useTitle } from "../hooks/useTitle";

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

function RankBadge({ rank }: { rank: number }) {
  if (rank <= 3) {
    return <span className={"sk-rank sk-rank-top sk-rank-" + rank}>{rank}</span>;
  }
  return <span className="sk-rank">{rank}</span>;
}

export default function SkillStats() {
  useTitle("Skill Stats", "Skill demand analysis — top skills, match rates, and skill combinations.");
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

  if (loading) {
    return (
      <>
        <div className="page-header"><h2>Skills</h2></div>
        <div className="st-loading">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="pf-skeleton pf-skeleton-line" style={{ height: 52, width: "100%" }} />
          ))}
        </div>
      </>
    );
  }

  if (skills.length === 0) {
    return (
      <>
        <div className="page-header"><h2>Skills</h2></div>
        <div className="st-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="16 18 22 12 16 6" />
            <polyline points="8 6 2 12 8 18" />
          </svg>
          <h3>No skill data</h3>
          <p>Skill statistics will appear once applications are sent.</p>
        </div>
      </>
    );
  }

  const topSkill = skills[0];
  const totalSkillHits = skills.reduce((sum, s) => sum + s.total, 0);
  const maxCount = topSkill?.total || 1;

  return (
    <>
      <div className="page-header">
        <h2>Skills <span className="count">({totalApps} applications)</span></h2>
      </div>

      {/* Summary */}
      <div className="st-summary-row">
        <div className="st-summary-card">
          <span className="st-summary-value">{skills.length}</span>
          <span className="st-summary-label">Unique Skills</span>
        </div>
        <div className="st-summary-card">
          <span className="st-summary-value">{totalSkillHits}</span>
          <span className="st-summary-label">Total Mentions</span>
        </div>
        <div className="st-summary-card">
          <span className="st-summary-value">{topSkill?.skill_name || "—"}</span>
          <span className="st-summary-label">Most Used</span>
        </div>
        <div className="st-summary-card">
          <span className="st-summary-value">{combos.length}</span>
          <span className="st-summary-label">Skill Combos</span>
        </div>
      </div>

      {/* Skill Combinations */}
      {combos.length > 0 && (
        <div className="st-card">
          <h3 className="st-card-title">Top Skill Combinations</h3>
          <p className="st-card-subtitle">Pairs of skills that frequently appear together in job descriptions.</p>
          <div className="sk-combo-grid">
            {combos.map((c, i) => (
              <div key={i} className="sk-combo-card">
                <div className="sk-combo-rank-row">
                  <RankBadge rank={i + 1} />
                  <span className="sk-combo-freq">{c.count}x</span>
                </div>
                <div className="sk-combo-tags">
                  {c.skills.map((s, j) => (
                    <span key={j}>
                      <span className="skill-tag large">{s}</span>
                      {j < c.skills.length - 1 && (
                        <svg className="sk-combo-connector" width="20" height="12" viewBox="0 0 20 12">
                          <line x1="0" y1="6" x2="14" y2="6" stroke="currentColor" strokeWidth="1.5" strokeDasharray="3 2" />
                          <circle cx="17" cy="6" r="2" fill="currentColor" />
                        </svg>
                      )}
                    </span>
                  ))}
                </div>
                <div className="sk-combo-bar">
                  <div className="sk-combo-bar-fill" style={{ width: `${(c.count / (combos[0]?.count || 1)) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Skills */}
      <div className="st-card">
        <h3 className="st-card-title">All Skills</h3>
        <p className="st-card-subtitle">Ranked by frequency of appearance across all applications.</p>
        <div className="sk-list">
          {skills.map((s, i) => (
            <div key={s.skill_name} className="sk-row">
              <RankBadge rank={i + 1} />
              <div className="sk-row-name">{s.skill_name}</div>
              <div className="sk-row-bar">
                <div className="sk-row-bar-track">
                  <div className="sk-row-bar-fill" style={{ width: `${(s.total / maxCount) * 100}%` }} />
                </div>
              </div>
              <div className="sk-row-metrics">
                <div className="sk-metric">
                  <span className="sk-metric-val">{s.total}</span>
                  <span className="sk-metric-lbl">total</span>
                </div>
                <div className="sk-metric">
                  <span className="sk-metric-val">{s.found_count}</span>
                  <span className="sk-metric-lbl">in JD</span>
                </div>
                <div className="sk-metric">
                  <span className="sk-metric-val">{s.highlighted_count}</span>
                  <span className="sk-metric-lbl">used</span>
                </div>
                <div className="sk-metric">
                  <span className="sk-metric-val">{s.pct}%</span>
                  <span className="sk-metric-lbl">share</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
