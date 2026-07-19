import { useEffect, useState, useRef } from "react";
import { api } from "../api/client";
import { useTitle } from "../hooks/useTitle";

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
  useTitle("Profile", "Manage your skills, experience, and job matching preferences.");
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout>>();

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeInfo, setResumeInfo] = useState<{ has_resume: boolean; filename?: string; size_kb?: number }>({ has_resume: false });
  const [resumeUploading, setResumeUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [secEmail, setSecEmail] = useState("");
  const [secPassword, setSecPassword] = useState("");
  const [secStatus, setSecStatus] = useState<{ has_credentials: boolean; sender_email: string }>({ has_credentials: false, sender_email: "" });
  const [secSaving, setSecSaving] = useState(false);
  const [secInitialized, setSecInitialized] = useState(false);

  useEffect(() => {
    api.profile.get().then((d: any) => {
      setProfile(d.profile || d);
      setLoading(false);
    });
    api.profile.getResume().then((d: any) => setResumeInfo(d));
    api.profile.getSecurity().then((d: any) => {
      setSecStatus(d);
      setSecEmail(d.sender_email || "");
      setSecInitialized(true);
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

  const handleResumeUpload = async () => {
    if (!resumeFile) return;
    setResumeUploading(true);
    try {
      await api.profile.uploadResume(resumeFile);
      setResumeInfo({ has_resume: true, filename: resumeFile.name, size_kb: Math.round(resumeFile.size / 1024) });
      setResumeFile(null);
      showToast("success", "Resume uploaded successfully.");
    } catch (e: any) {
      showToast("error", e.message || "Failed to upload resume.");
    }
    setResumeUploading(false);
  };

  const handleResumeDelete = async () => {
    try {
      await api.profile.deleteResume();
      setResumeInfo({ has_resume: false });
      showToast("success", "Resume deleted.");
    } catch {
      showToast("error", "Failed to delete resume.");
    }
  };

  const handleSecSave = async () => {
    if (!secEmail || !secPassword) return;
    setSecSaving(true);
    try {
      await api.profile.saveSecurity(secEmail, secPassword);
      setSecStatus({ has_credentials: true, sender_email: secEmail });
      setSecPassword("");
      showToast("success", "Credentials saved securely.");
    } catch (e: any) {
      showToast("error", e.message || "Failed to save credentials.");
    }
    setSecSaving(false);
  };

  const handleSecDelete = async () => {
    try {
      await api.profile.deleteSecurity();
      setSecStatus({ has_credentials: false, sender_email: "" });
      setSecEmail("");
      setSecPassword("");
      showToast("success", "Credentials removed.");
    } catch {
      showToast("error", "Failed to remove credentials.");
    }
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

        {/* Resume */}
        <SectionCard title="Resume" description="Upload your resume PDF. Used when sending job applications via email.">
          <div className="pf-resume">
            {resumeInfo.has_resume && !resumeFile ? (
              <div className="pf-resume-info">
                <div className="pf-resume-file">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  <div>
                    <span className="pf-resume-name">{resumeInfo.filename}</span>
                    <span className="pf-resume-size">{resumeInfo.size_kb} KB</span>
                  </div>
                </div>
                <div className="pf-resume-actions">
                  <button type="button" className="pf-btn-secondary" onClick={() => fileInputRef.current?.click()}>Replace</button>
                  <button type="button" className="pf-btn-danger" onClick={handleResumeDelete}>Delete</button>
                </div>
              </div>
            ) : resumeFile ? (
              <div className="pf-resume-info">
                <div className="pf-resume-file">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  <div>
                    <span className="pf-resume-name">{resumeFile.name}</span>
                    <span className="pf-resume-size">{Math.round(resumeFile.size / 1024)} KB</span>
                  </div>
                </div>
                <div className="pf-resume-actions">
                  <button type="button" className="pf-btn-primary" onClick={handleResumeUpload} disabled={resumeUploading}>
                    {resumeUploading ? "Uploading..." : "Upload"}
                  </button>
                  <button type="button" className="pf-btn-secondary" onClick={() => setResumeFile(null)}>Cancel</button>
                </div>
              </div>
            ) : (
              <div
                className="pf-resume-drop"
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add("pf-drop-active"); }}
                onDragLeave={(e) => e.currentTarget.classList.remove("pf-drop-active")}
                onDrop={(e) => {
                  e.preventDefault();
                  e.currentTarget.classList.remove("pf-drop-active");
                  const file = e.dataTransfer.files[0];
                  if (file && file.name.endsWith(".pdf")) setResumeFile(file);
                }}
              >
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                <span>Drop a PDF here or click to browse</span>
                <span className="pf-hint">Maximum 5 MB</span>
              </div>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              style={{ display: "none" }}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) setResumeFile(file);
                e.target.value = "";
              }}
            />
          </div>
        </SectionCard>

        {/* Security */}
        <SectionCard title="Security" description="Email credentials for sending job applications. Stored encrypted on the server.">
          {secInitialized && (
            <div className="pf-security">
              {secStatus.has_credentials && (
                <div className="pf-sec-status">
                  <span className="pf-sec-dot pf-sec-dot-green" />
                  <span>Configured: {secStatus.sender_email}</span>
                </div>
              )}
              <div className="pf-grid pf-grid-2">
                <FormField label="Sender email" hint="Gmail address to send applications from">
                  <input
                    className="pf-input"
                    type="email"
                    value={secEmail}
                    onChange={(e) => setSecEmail(e.target.value)}
                    placeholder="your-email@gmail.com"
                  />
                </FormField>
                <FormField label="App password" hint="Gmail App Password (not your main password)">
                  <input
                    className="pf-input"
                    type="password"
                    value={secPassword}
                    onChange={(e) => setSecPassword(e.target.value)}
                    placeholder={secStatus.has_credentials ? "Enter new password to update" : "xxxx-xxxx-xxxx-xxxx"}
                    autoComplete="off"
                  />
                </FormField>
              </div>
              <div className="pf-sec-actions">
                <button type="button" className="pf-btn-primary" onClick={handleSecSave} disabled={secSaving || !secEmail || !secPassword}>
                  {secSaving ? "Saving..." : secStatus.has_credentials ? "Update Credentials" : "Save Credentials"}
                </button>
                {secStatus.has_credentials && (
                  <button type="button" className="pf-btn-danger" onClick={handleSecDelete}>Remove</button>
                )}
              </div>
            </div>
          )}
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
