import { useEffect, useState } from "react";
import { api } from "../api/client";

interface ProfileData {
  name: string;
  email: string;
  role: string;
  experience_years: number;
  experience_min: number;
  experience_max: number;
  location: string;
  skills: Record<string, string[]>;
  projects: { name: string; description: string; tech: string; link: string }[];
  looking_for: string[];
  languages: string[];
  [key: string]: unknown;
}

export default function Profile() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.profile.get().then((d: any) => {
      setProfile(d.profile || d);
      setLoading(false);
    });
  }, []);

  const handleChange = (field: string, value: string | number | string[]) => {
    if (!profile) return;
    setProfile({ ...profile, [field]: value });
  };

  const handleSkillChange = (category: string, value: string) => {
    if (!profile) return;
    const skills = { ...profile.skills, [category]: value.split(",").map((s) => s.trim()).filter(Boolean) };
    setProfile({ ...profile, skills });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const res = await api.profile.update(profile as unknown as Record<string, unknown>);
      setMessage((res as any).message || "Profile saved successfully.");
    } catch (err) {
      setError("Failed to save profile. Please check all required fields.");
    }
    setSaving(false);
  };

  if (loading) return <div className="empty-guidance"><h3>Loading...</h3></div>;
  if (!profile) return <div className="empty-guidance"><h3>Profile not found</h3></div>;

  return (
    <>
      <div className="page-header">
        <h2>Profile</h2>
      </div>

      {message && <div className="card card-dashboard" style={{ padding: "1rem 1.5rem", marginBottom: "1rem", borderLeft: "3px solid var(--accent, #6c63ff)" }}>{message}</div>}
      {error && <div className="card card-dashboard" style={{ padding: "1rem 1.5rem", marginBottom: "1rem", borderLeft: "3px solid #ff4757" }}>{error}</div>}

      <div className="card card-dashboard" style={{ padding: "1.5rem" }}>
        <form onSubmit={handleSubmit}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div className="form-group">
              <label style={{ display: "block", marginBottom: "0.3rem", fontWeight: 600 }}>Name *</label>
              <input
                type="text"
                className="form-control"
                value={profile.name || ""}
                onChange={(e) => handleChange("name", e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label style={{ display: "block", marginBottom: "0.3rem", fontWeight: 600 }}>Email *</label>
              <input
                type="email"
                className="form-control"
                value={profile.email || ""}
                onChange={(e) => handleChange("email", e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label style={{ display: "block", marginBottom: "0.3rem", fontWeight: 600 }}>Role *</label>
              <input
                type="text"
                className="form-control"
                value={profile.role || ""}
                onChange={(e) => handleChange("role", e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label style={{ display: "block", marginBottom: "0.3rem", fontWeight: 600 }}>Location *</label>
              <input
                type="text"
                className="form-control"
                value={profile.location || ""}
                onChange={(e) => handleChange("location", e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label style={{ display: "block", marginBottom: "0.3rem", fontWeight: 600 }}>Experience (years) *</label>
              <input
                type="number"
                className="form-control"
                value={profile.experience_years || 0}
                onChange={(e) => handleChange("experience_years", parseInt(e.target.value) || 0)}
                min={0}
                required
              />
            </div>
            <div className="form-group">
              <label style={{ display: "block", marginBottom: "0.3rem", fontWeight: 600 }}>Min Experience</label>
              <input
                type="number"
                className="form-control"
                value={profile.experience_min || 0}
                onChange={(e) => handleChange("experience_min", parseInt(e.target.value) || 0)}
                min={0}
              />
            </div>
            <div className="form-group">
              <label style={{ display: "block", marginBottom: "0.3rem", fontWeight: 600 }}>Max Experience</label>
              <input
                type="number"
                className="form-control"
                value={profile.experience_max || 3}
                onChange={(e) => handleChange("experience_max", parseInt(e.target.value) || 0)}
                min={0}
              />
            </div>
          </div>

          {/* Skills */}
          <h3 style={{ marginTop: "1.5rem", marginBottom: "0.75rem" }}>Skills</h3>
          {Object.entries(profile.skills || {}).map(([category, skillList]) => (
            <div key={category} className="form-group" style={{ marginBottom: "0.75rem" }}>
              <label style={{ display: "block", marginBottom: "0.3rem", fontWeight: 600, textTransform: "capitalize" }}>
                {category.replace(/_/g, " ")}
              </label>
              <input
                type="text"
                className="form-control"
                value={(skillList || []).join(", ")}
                onChange={(e) => handleSkillChange(category, e.target.value)}
                placeholder="Comma-separated skills"
              />
            </div>
          ))}

          {/* Looking for */}
          <div className="form-group" style={{ marginTop: "1rem" }}>
            <label style={{ display: "block", marginBottom: "0.3rem", fontWeight: 600 }}>Looking For (comma-separated)</label>
            <input
              type="text"
              className="form-control"
              value={(profile.looking_for || []).join(", ")}
              onChange={(e) => handleChange("looking_for", e.target.value.split(",").map((s) => s.trim()).filter(Boolean))}
            />
          </div>

          {/* Languages */}
          <div className="form-group">
            <label style={{ display: "block", marginBottom: "0.3rem", fontWeight: 600 }}>Languages (comma-separated)</label>
            <input
              type="text"
              className="form-control"
              value={(profile.languages || []).join(", ")}
              onChange={(e) => handleChange("languages", e.target.value.split(",").map((s) => s.trim()).filter(Boolean))}
            />
          </div>

          {/* Projects */}
          <h3 style={{ marginTop: "1.5rem", marginBottom: "0.75rem" }}>Projects</h3>
          {(profile.projects || []).length === 0 && (
            <p style={{ color: "var(--text-secondary, #888)", fontSize: "0.9rem" }}>No projects added yet.</p>
          )}
          {(profile.projects || []).map((proj, i) => (
            <div key={i} className="card" style={{ padding: "1rem", marginBottom: "0.75rem", background: "var(--bg-secondary, #1a1a2e)" }}>
              <strong>{proj.name}</strong>
              <div style={{ fontSize: "0.85rem", color: "var(--text-secondary, #888)" }}>{proj.tech}</div>
              <p style={{ margin: "0.5rem 0" }}>{proj.description}</p>
              {proj.link && <a href={proj.link} target="_blank" rel="noopener noreferrer" style={{ fontSize: "0.85rem" }}>{proj.link}</a>}
            </div>
          ))}

          <button type="submit" className="btn btn-primary" disabled={saving} style={{ marginTop: "1rem" }}>
            {saving ? "Saving..." : "Save Profile"}
          </button>
        </form>
      </div>
    </>
  );
}
