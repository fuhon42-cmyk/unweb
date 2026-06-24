"use client";

import { useState, useEffect } from "react";
import CopyButton from "@/components/CopyButton";
import { extract, type ExtractResponse } from "@/lib/api";

const API_BASE = "https://unweb-production-6f69.up.railway.app";

interface SiteItem { id: string; site_name: string; url: string; content?: string }
interface DashboardMetrics { total_extracts: number; total_publishes: number; unique_urls_24h: number }

interface DashboardMetrics {
  total_extracts: number;
  total_publishes: number;
  unique_urls_24h: number;
}

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    active: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    error: "bg-red-500/10 text-red-400 border-red-500/20",
    pending: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${colors[status] || ""}`}
    >
      {status}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Stat card
// ---------------------------------------------------------------------------

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: "emerald" | "cyan" | "violet";
}) {
  const accentColors: Record<string, string> = {
    emerald: "text-emerald-400",
    cyan: "text-cyan-400",
    violet: "text-violet-400",
  };

  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900/50 px-6 py-5">
      <p className="text-sm text-zinc-300">{label}</p>
      <p className={`mt-1 text-2xl font-bold tracking-tight ${accentColors[accent]}`}>
        {value}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chevron icon
// ---------------------------------------------------------------------------

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className={`h-4 w-4 transition-transform ${open ? "rotate-90" : ""}`}
    >
      <path
        fillRule="evenodd"
        d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
        clipRule="evenodd"
      />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const [url, setUrl] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [result, setResult] = useState<ExtractResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resultOpen, setResultOpen] = useState(false);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [sites, setSites] = useState<SiteItem[]>([]);
  const [apiKey, setApiKey] = useState("");

  async function fetchAll(key: string) {
    try {
      const [mr, sr] = await Promise.all([
        fetch(`${API_BASE}/api/v1/metrics`, { headers: { "X-API-Key": key } }),
        fetch(`${API_BASE}/api/v1/sites`, { headers: { "X-API-Key": key } }),
      ]);
      if (mr.ok) { const d = await mr.json(); setMetrics(d.dashboard); }
      if (sr.ok) { const d = await sr.json(); setSites(Array.isArray(d) ? d : []); }
    } catch {}
  }

  useEffect(() => {
    fetchAll("any");
  }, []);

  const stats = metrics ?? {
    total_extracts: 0,
    total_publishes: 0,
    unique_urls_24h: 0,
  };

  async function handleExtract(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;

    setExtracting(true);
    setError(null);
    setResult(null);
    setResultOpen(false);

    try {
      const data = await extract(url, apiKey);
      setResult(data);
      setResultOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Extraction failed");
    } finally {
      setExtracting(false);
    }
  }

  return (
    <div className="min-h-full bg-black text-zinc-100">
      <div className="mx-auto max-w-6xl px-6 py-12">
        {/* Header */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="mt-2 text-zinc-300">
            Overview of your Unweb account and activity.
          </p>
        </div>

        {/* Stats cards */}
        <div className="mb-10 grid gap-6 sm:grid-cols-3">
          <StatCard
            label="Total Extracts"
            value={stats.total_extracts.toLocaleString()}
            accent="emerald"
          />
          <StatCard
            label="Sites Published"
            value={stats.total_publishes.toString()}
            accent="cyan"
          />
          <StatCard
            label="Unique URLs (24h)"
            value={stats.unique_urls_24h.toLocaleString()}
            accent="violet"
          />
        </div>

        {/* API key */}
        <section className="mb-10">
          <h2 className="mb-4 text-lg font-semibold">API Key</h2>
          <div className="flex items-center gap-3 rounded-xl border border-zinc-700 bg-zinc-900/50 px-5 py-4">
            <code className="min-w-0 flex-1 truncate font-mono text-sm text-zinc-300">
              {apiKey}
            </code>
            <CopyButton text={apiKey} label="Copy" />
          </div>
        </section>

        {/* Sites list */}
        <section className="mb-10">
          <h2 className="mb-4 text-lg font-semibold">Sites</h2>
          <div className="overflow-hidden rounded-xl border border-zinc-700">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-700 bg-zinc-900/50">
                  <th className="px-5 py-3 font-medium text-zinc-300">Name</th>
                  <th className="px-5 py-3 font-medium text-zinc-300">URL</th>
                  <th className="px-5 py-3 font-medium text-zinc-300">Status</th>
                  <th className="px-5 py-3 font-medium text-zinc-300">
                    Last Scraped
                  </th>
                </tr>
              </thead>
              <tbody>
                {sites.map((site) => (
                  <tr
                    key={site.id}
                    className="border-b border-zinc-700 last:border-0"
                  >
                    <td className="px-5 py-4 font-medium">{site.site_name}</td>
                    <td className="max-w-0 px-5 py-4 font-mono text-xs text-zinc-300">
                      <span className="block truncate">{site.url}</span>
                    </td>
                    <td className="px-5 py-4">
                      <StatusBadge status={"active"} />
                    </td>
                    <td className="px-5 py-4 text-zinc-300">
                      {site.url}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Quick extract test */}
        <section>
          <h2 className="mb-4 text-lg font-semibold">Quick Extract Test</h2>
          <form onSubmit={handleExtract} className="flex gap-3">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              required
              className="min-w-0 flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            />
            <button
              type="submit"
              disabled={extracting}
              className="inline-flex h-10 shrink-0 items-center gap-2 rounded-lg bg-emerald-500 px-5 text-sm font-semibold text-black transition-colors hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {extracting ? "Extracting..." : "Extract"}
            </button>
          </form>

          {error && (
            <div className="mt-4 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {result && (
            <div className="mt-4 overflow-hidden rounded-xl border border-zinc-800">
              <button
                onClick={() => setResultOpen((o) => !o)}
                className="flex w-full items-center gap-2 bg-zinc-900/50 px-5 py-3 text-left text-sm font-medium text-zinc-300 transition-colors hover:bg-zinc-800/50"
              >
                <ChevronIcon open={resultOpen} />
                Response
              </button>
              {resultOpen && (
                <pre className="overflow-x-auto border-t border-zinc-800 px-5 py-4 font-mono text-xs leading-relaxed text-zinc-300">
                  {JSON.stringify(result, null, 2)}
                </pre>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
