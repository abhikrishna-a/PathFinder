import type { PaginatedResponse, Job, JobDetail, Application } from "../types";

const BASE = "/api/v1";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  jobs: {
    list(params: Record<string, string> = {}): Promise<PaginatedResponse<Job>> {
      const qs = new URLSearchParams(params).toString();
      return get(`/jobs/${qs ? `?${qs}` : ""}`);
    },
    detail(id: number): Promise<JobDetail> {
      return get(`/jobs/${id}/`);
    },
  },
  applications: {
    list(params: Record<string, string> = {}): Promise<PaginatedResponse<Application>> {
      const qs = new URLSearchParams(params).toString();
      return get(`/applications/${qs ? `?${qs}` : ""}`);
    },
  },
  stats: {
    overview(): Promise<Record<string, unknown>> {
      return get("/stats/overview/");
    },
    skills(): Promise<Record<string, unknown>> {
      return get("/stats/skills/");
    },
    companies(): Promise<Record<string, unknown>> {
      return get("/stats/companies/");
    },
    locations(): Promise<Record<string, unknown>> {
      return get("/stats/locations/");
    },
  },
  profile: {
    get(): Promise<Record<string, unknown>> {
      return get("/profile/");
    },
    update(data: Record<string, unknown>): Promise<Record<string, unknown>> {
      return fetch(`${BASE}/profile/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile: data }),
      }).then((r) => {
        if (!r.ok) throw new Error(`API error: ${r.status}`);
        return r.json();
      });
    },
  },
  webApply: {
    list(): Promise<Record<string, unknown>> {
      return get("/web-apply/");
    },
  },
  missingEmails: {
    list(): Promise<Record<string, unknown>> {
      return get("/missing-emails/");
    },
  },
  fetcher: {
    run(): Promise<Record<string, unknown>> {
      return fetch(`${BASE}/fetcher/run/`, { method: "POST" }).then((r) => {
        if (!r.ok) throw new Error(`API error: ${r.status}`);
        return r.json();
      });
    },
    status(): Promise<Record<string, unknown>> {
      return get("/fetcher/status/");
    },
  },
};
