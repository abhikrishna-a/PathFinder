import { useEffect, useState, useRef } from "react";
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

function UserAvatar({ name }: { name: string }) {
  const initials = name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  return <div className="profile-avatar">{initials}</div>;
}

function SectionCard({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="profile-section">
      <div className="profile-section-header">
        <h3 className="profile-section-title">{title}</h3>
        {description && <p className="profile-section-desc">{description}</p>}
      </div>
      <div className="profile-section-body">{children}</div>
    </div>
  );
}

function FormField({ label, hint, children, className = "" }: { label: string; hint?: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`pf-field ${className}`}>
      <label className="pf-label">{label}</label>
      {hint && <span className="pf-hint">{hint}</span>}
      {children}
    </div>
  );
}

export default function Profile() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    api.profile.get().then((d: any) => {
      setProfile(d.profile || d);
      setLoading(false);
    });
  }, []);

  function showToast(type: "success" | "error", msg: string) {
    setToast({ type, msg });
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 4000);
  }

  const set = (field: string, value: string | number | string[]) => {
    if (!profile) return;
    setProfile({ ...profile, [field]: value });
  };

  const setSkill = (category: string, raw: string) => {
    if (!profile) return;
    const skills = {
      ...profile.skills,
      [category]: raw
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    };
    setProfile({ ...profile, skills });
  };

  const addProject = () => {
    if (!profile) return;
    setProfile({
      ...profile,
      projects: [...(profile.projects || []), { name: "", description: "", tech: "", link: "" }],
    });
  };

  const updateProject = (i: number, field: string, value: string) => {
    if (!profile) return;
    const projects = [...(profile.projects || [])];
    projects[i] = { ...projects[i], [field]: value };
    setProfile({ ...profile, projects });
  };

  const removeProject = (i: number) => {
    if (!profile) return;
    const projects = (profile.projects || []).filter((_, idx) => idx !== i);
    setProfile({ ...profile, projects });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    setSaving(true);
    try {
      const res = await api.profile.update(profile as unknown as Record<string, unknown>);
      showToast("success", (res as any).message || "Profile saved successfully.");
    } catch {
      showToast("error", "Failed to save profile. Please check all required fields.");
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="profile-loading">
        <div className="pf-skeleton pf-skeleton-avatar" />
        <div className="pf-skeleton pf-skeleton-line" style={{ width: "40%" }} />
        <div className="pf-skeleton pf-skeleton-line" style={{ width: "60%" }} />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="empty-guidance">
        <h3>Profile not found</h3>
      </div>
    );
  }

  return (
    <>
      {toast && (
        <div className={`pf-toast ${toast.type}`}>{toast.msg}</div>
      )}

      {/* Hero */}
      <div className="profile-hero">
        <UserAvatar name={profile.name || "?"} />
        <div className="profile-hero-info">
          <h2>{profile.name || "Unnamed"}</h2>
          <p>
            {profile.role}
            {profile.location ? ` · ${profile.location}` : ""}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Personal Info */}
        <SectionCard title="Personal Information" description="Basic contact and identity details.">
          <div className="pf-grid pf-grid-2">
            <FormField label="Full name">
              <input className="pf-input" type="text" value={profile.name || ""} onChange={(e) => set("name", e.target.value)} required />
            </FormField>
            <FormField label="Email">
              <input className="pf-input" type="email" value={profile.email || ""} onChange={(e) => set("email", e.target.value)} required />
            </FormField>
            <FormField label="Role / Title">
              <input className="pf-input" type="text" value={profile.role || ""} onChange={(e) => set("role", e.target.value)} required />
            </FormField>
            <FormField label="Location">
              <input className="pf-input" type="text" value={profile.location || ""} onChange={(e) => set("location", e.target.value)} required />
            </FormField>
          </div>
        </SectionCard>

        {/* Experience */}
        <SectionCard title="Experience" description="Years of experience and preferred range for job matching.">
          <div className="pf-grid pf-grid-3">
            <FormField label="Years of experience" hint="Total professional experience">
              <input className="pf-input" type="number" min={0} value={profile.experience_years || 0} onChange={(e) => set("experience_years", parseInt(e.target.value) || 0)} required />
            </FormField>
            <FormField label="Minimum (years)" hint="Lower bound for matching">
              <input className="pf-input" type="number" min={0} value={profile.experience_min || 0} onChange={(e) => set("experience_min", parseInt(e.target.value) || 0)} />
            </FormField>
            <FormField label="Maximum (years)" hint="Upper bound for matching">
              <input className="pf-input" type="number" min={0} value={profile.experience_max || 3} onChange={(e) => set("experience_max", parseInt(e.target.value) || 0)} />
            </FormField>
          </div>
        </SectionCard>

        {/* Skills */}
        <SectionCard title="Skills" description="Comma-separated lists per category. Used for job matching and scoring.">
          <div className="pf-grid pf-grid-2">
            {Object.entries(profile.skills || {}).map(([category, skillList]) => (
              <FormField key={category} label={category.replace(/_/g, " ")} className="pf-field-capitalize">
                <input
                  className="pf-input"
                  type="text"
                  value={(skillList || []).join(", ")}
                  onChange={(e) => setSkill(category, e.target.value)}
                  placeholder="e.g. Django, React, PostgreSQL"
                />
              </FormField>
            ))}
          </div>
        </SectionCard>

        {/* Preferences */}
        <SectionCard title="Preferences" description="Job type preferences and languages.">
          <div className="pf-grid pf-grid-2">
            <FormField label="Looking for" hint="Target roles, comma-separated">
              <input
                className="pf-input"
                type="text"
                value={(profile.looking_for || []).join(", ")}
                onChange={(e) =>
                  set(
                    "looking_for",
                    e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean)
                  )
                }
              />
            </FormField>
            <FormField label="Languages" hint="Spoken languages, comma-separated">
              <input
                className="pf-input"
                type="text"
                value={(profile.languages || []).join(", ")}
                onChange={(e) =>
                  set(
                    "languages",
                    e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean)
                  )
                }
              />
            </FormField>
          </div>
        </SectionCard>

        {/* Projects */}
        <SectionCard title="Projects" description="Key projects showcased in cover letters.">
          {(profile.projects || []).length === 0 && (
            <div className="pf-empty-projects">
              <p>No projects added yet. Projects are mentioned in cover letters to demonstrate relevant experience.</p>
            </div>
          )}
          {(profile.projects || []).map((proj, i) => (
            <div key={i} className="pf-project-card">
              <div className="pf-project-header">
                <span className="pf-project-num">Project {i + 1}</span>
                <button type="button" className="pf-project-remove" onClick={() => removeProject(i)} title="Remove project">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
              <div className="pf-grid pf-grid-2">
                <FormField label="Name">
                  <input className="pf-input" type="text" value={proj.name} onChange={(e) => updateProject(i, "name", e.target.value)} placeholder="e.g. EchOo" />
                </FormField>
                <FormField label="Tech stack">
                  <input className="pf-input" type="text" value={proj.tech} onChange={(e) => updateProject(i, "tech", e.target.value)} placeholder="e.g. Django, React, PostgreSQL" />
                </FormField>
              </div>
              <FormField label="Description">
                <textarea className="pf-input pf-textarea" value={proj.description} onChange={(e) => updateProject(i, "description", e.target.value)} rows={2} placeholder="Brief description of what you built and your role..." />
              </FormField>
              <FormField label="Link" hint="Optional">
                <input className="pf-input" type="url" value={proj.link} onChange={(e) => updateProject(i, "link", e.target.value)} placeholder="https://..." />
              </FormField>
            </div>
          ))}
          <button type="button" className="pf-btn-add" onClick={addProject}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add project
          </button>
        </SectionCard>

        {/* Sticky save bar */}
        <div className="pf-save-bar">
          <button type="submit" className="pf-btn-save" disabled={saving}>
            {saving ? (
              <span className="pf-save-loading">
                <span className="spinner" /> Saving...
              </span>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                  <polyline points="17 21 17 13 7 13 7 21" />
                  <polyline points="7 3 7 8 15 8" />
                </svg>
                Save profile
              </>
            )}
          </button>
        </div>
      </form>
    </>
  );
}
