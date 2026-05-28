import { FetchLatestButton } from "@/components/fetch-latest-button";
import { Issue, IssueDashboard } from "@/components/issue-dashboard";
import { MetricCard } from "@/components/metric-card";

type Overview = {
  sources: Record<string, number>;
  top_issue_categories: { name: string; count: number }[];
  top_issue_subcategories: { name: string; count: number }[];
  top_skills: { name: string; count: number }[];
  top_technologies: { name: string; count: number }[];
  unresolved_rate: number;
  raw_items_count: number;
  normalized_issues_count: number;
  source_date_range: { start: string | null; end: string | null };
  fetched_date_range: { start: string | null; end: string | null };
};

async function getOverview(): Promise<Overview> {
  const baseUrl = process.env.API_BASE_URL || "http://localhost:8000";
  try {
    const response = await fetch(`${baseUrl}/api/analytics/overview`, { cache: "no-store" });
    if (!response.ok) throw new Error("overview unavailable");
    return response.json();
  } catch {
    return {
      sources: {},
      top_issue_categories: [],
      top_issue_subcategories: [],
      top_skills: [],
      top_technologies: [],
      unresolved_rate: 0,
      raw_items_count: 0,
      normalized_issues_count: 0,
      source_date_range: { start: null, end: null },
      fetched_date_range: { start: null, end: null }
    };
  }
}

async function getIssues(): Promise<Issue[]> {
  const baseUrl = process.env.API_BASE_URL || "http://localhost:8000";
  try {
    const response = await fetch(`${baseUrl}/api/issues?limit=200`, { cache: "no-store" });
    if (!response.ok) throw new Error("issues unavailable");
    return response.json();
  } catch {
    return [];
  }
}

export default async function Home() {
  const overview = await getOverview();
  const issues = await getIssues();
  const sourceCount = overview.normalized_issues_count || Object.values(overview.sources).reduce((total, count) => total + count, 0);
  const clientApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  return (
    <main className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold text-ink">OpenAI Support Intelligence</h1>
            <p className="text-sm text-slate-600">Developer issue analytics across GitHub and OpenAI Community</p>
          </div>
          <FetchLatestButton apiBaseUrl={clientApiBaseUrl} />
        </div>
      </header>

      <div className="mx-auto max-w-7xl space-y-6 px-6 py-6">
        <section className="grid gap-4 md:grid-cols-4">
          <MetricCard label="Normalized Issues" value={String(sourceCount)} detail="Stored in unified issue schema" />
          <MetricCard
            label="Unresolved Rate"
            value={`${Math.round(overview.unresolved_rate * 100)}%`}
            detail="Based on latest extraction run"
          />
          <MetricCard label="Raw Items" value={String(overview.raw_items_count)} detail="Immutable source payloads" />
          <MetricCard label="Active Sources" value={String(Object.keys(overview.sources).length)} detail="GitHub and Community-ready" />
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <section className="rounded-md border border-line bg-white p-4">
            <h2 className="text-sm font-semibold text-ink">Issue Date Range</h2>
            <p className="mt-2 text-sm text-slate-600">
              Source issues cover {formatDate(overview.source_date_range.start)} to {formatDate(overview.source_date_range.end)}.
            </p>
          </section>
          <section className="rounded-md border border-line bg-white p-4">
            <h2 className="text-sm font-semibold text-ink">Fetch Date Range</h2>
            <p className="mt-2 text-sm text-slate-600">
              Payloads were fetched from {formatDate(overview.fetched_date_range.start)} to {formatDate(overview.fetched_date_range.end)}.
            </p>
          </section>
        </section>

        <IssueDashboard issues={issues} apiBaseUrl={clientApiBaseUrl} />
      </div>
    </main>
  );
}

function formatDate(value: string | null) {
  if (!value) return "No data";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}
