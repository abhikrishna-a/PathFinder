import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Overview from "./pages/Overview";
import Jobs from "./pages/Jobs";
import JobDetail from "./pages/JobDetail";
import Applications from "./pages/Applications";
import WebApply from "./pages/WebApply";
import MissingEmails from "./pages/MissingEmails";
import SkillStats from "./pages/SkillStats";
import CompanyStats from "./pages/CompanyStats";
import LocationStats from "./pages/LocationStats";
import Profile from "./pages/Profile";

function Navbar() {
  const links = [
    { to: "/", label: "Overview" },
    { to: "/jobs", label: "Jobs" },
    { to: "/applications", label: "Applications" },
    { to: "/web-apply", label: "Web Apply" },
    { to: "/missing-emails", label: "Missing" },
    { to: "/stats/skills", label: "Skills" },
    { to: "/stats/companies", label: "Companies" },
    { to: "/stats/locations", label: "Locations" },
    { to: "/profile", label: "Profile" },
  ];

  return (
    <nav>
      <div className="nav-brand">
        <div className="logo">P</div>
        PathFinder
        <span className="version-badge">v0.1.0</span>
      </div>
      <div className="nav-links">
        {links.map((l) => (
          <NavLink key={l.to} to={l.to} className={({ isActive }) => isActive ? "active" : ""} end>
            {l.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/jobs/:id" element={<JobDetail />} />
          <Route path="/applications" element={<Applications />} />
          <Route path="/web-apply" element={<WebApply />} />
          <Route path="/missing-emails" element={<MissingEmails />} />
          <Route path="/stats/skills" element={<SkillStats />} />
          <Route path="/stats/companies" element={<CompanyStats />} />
          <Route path="/stats/locations" element={<LocationStats />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
      </main>
      <footer className="footer">
        PathFinder &mdash; Open Source Job Portal &middot; <a href="https://github.com" target="_blank" rel="noopener">GitHub</a>
      </footer>
    </BrowserRouter>
  );
}
