"use client";

import { useMemo, useState } from "react";

type Extraction = {
  problem_type: string;
  problem_subtype: string;
  root_cause: string | null;
  resolution_steps: string[];
  skills_required: string[];
  technologies_involved: string[];
  severity: string;
  was_resolved: boolean;
  resolution_confidence: number;
  issue_category: string;
  issue_subcategory: string;
  support_workflow_stage: string;
};

export type Issue = {
  id: string;
  source: string;
  title: string;
  original_text: string;
  normalized_text: string;
  author_handle: string | null;
  source_created_at: string | null;
  source_updated_at: string | null;
  status: string | null;
  canonical_url: string | null;
  latest_extraction: Extraction | null;
};

type GroupMode = "category" | "skill" | "technology" | "source";
type ViewMode = "intelligence" | "explorer" | "search";

export function IssueDashboard({ issues, apiBaseUrl }: { issues: Issue[]; apiBaseUrl: string }) {
  const [view, setView] = useState<ViewMode>("intelligence");
  const [groupMode, setGroupMode] = useState<GroupMode>("category");
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);
  const [expandedIssue, setExpandedIssue] = useState<string | null>(null);
  const [sourceFilter, setSourceFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Issue[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const groups = useMemo(() => groupIssues(issues, groupMode), [issues, groupMode]);
  const sources = Array.from(new Set(issues.map((issue) => issue.source))).sort();
  const statuses = Array.from(new Set(issues.map((issue) => issue.status || "unknown"))).sort();
  const filteredIssues = issues.filter((issue) => {
    return (
      (sourceFilter === "all" || issue.source === sourceFilter) &&
      (statusFilter === "all" || (issue.status || "unknown") === statusFilter)
    );
  });

  async function runSearch() {
    if (query.trim().length < 2) return;
    setIsSearching(true);
    setSearchError(null);
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/search/semantic?q=${encodeURIComponent(query.trim())}&limit=25`
      );
      if (!response.ok) throw new Error(`Search failed with HTTP ${response.status}`);
      setSearchResults((await response.json()) as Issue[]);
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : "Search failed");
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap gap-2 border-b border-line">
        <TabButton active={view === "intelligence"} label="Intelligence" onClick={() => setView("intelligence")} />
        <TabButton active={view === "explorer"} label="Issue Explorer" onClick={() => setView("explorer")} />
        <TabButton active={view === "search"} label="Search" onClick={() => setView("search")} />
      </div>

      {view === "intelligence" ? (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <ModeButton active={groupMode === "category"} label="Categories" onClick={() => setGroupMode("category")} />
            <ModeButton active={groupMode === "skill"} label="Skills" onClick={() => setGroupMode("skill")} />
            <ModeButton active={groupMode === "technology"} label="Technologies" onClick={() => setGroupMode("technology")} />
            <ModeButton active={groupMode === "source"} label="Sources" onClick={() => setGroupMode("source")} />
          </div>
          <div className="divide-y divide-line rounded-md border border-line bg-white">
            {groups.map((group) => (
              <section key={group.name}>
                <button
                  type="button"
                  className="flex w-full items-center justify-between px-4 py-3 text-left"
                  onClick={() => {
                    setExpandedGroup(expandedGroup === group.name ? null : group.name);
                    setExpandedIssue(null);
                  }}
                >
                  <span>
                    <span className="font-medium text-ink">{humanize(group.name)}</span>
                    {group.subline ? <span className="ml-2 text-sm text-slate-500">{group.subline}</span> : null}
                  </span>
                  <span className="text-sm font-semibold text-ink">{group.issues.length}</span>
                </button>
                {expandedGroup === group.name ? (
                  <IssueList
                    issues={group.issues}
                    expandedIssue={expandedIssue}
                    setExpandedIssue={setExpandedIssue}
                  />
                ) : null}
              </section>
            ))}
          </div>
        </div>
      ) : null}

      {view === "explorer" ? (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-3 rounded-md border border-line bg-white p-3">
            <Select label="Source" value={sourceFilter} values={["all", ...sources]} onChange={setSourceFilter} />
            <Select label="Status" value={statusFilter} values={["all", ...statuses]} onChange={setStatusFilter} />
          </div>
          <IssueList issues={filteredIssues} expandedIssue={expandedIssue} setExpandedIssue={setExpandedIssue} />
        </div>
      ) : null}

      {view === "search" ? (
        <div className="space-y-4">
          <div className="flex gap-2 rounded-md border border-line bg-white p-3">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") runSearch();
              }}
              className="min-w-0 flex-1 rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-accent"
              placeholder="Search issue text, titles, errors, SDKs..."
            />
            <button
              type="button"
              onClick={runSearch}
              disabled={isSearching || query.trim().length < 2}
              className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
            >
              {isSearching ? "Searching..." : "Search"}
            </button>
          </div>
          {searchError ? <p className="text-sm text-red-700">{searchError}</p> : null}
          <IssueList issues={searchResults} expandedIssue={expandedIssue} setExpandedIssue={setExpandedIssue} />
        </div>
      ) : null}
    </section>
  );
}

function IssueList({
  issues,
  expandedIssue,
  setExpandedIssue
}: {
  issues: Issue[];
  expandedIssue: string | null;
  setExpandedIssue: (id: string | null) => void;
}) {
  return (
    <div className="divide-y divide-line bg-white">
      {issues.map((issue) => (
        <article key={issue.id} className="px-4 py-3">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <a
                href={issue.canonical_url || "#"}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-accent hover:underline"
              >
                {issue.title}
              </a>
              <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
                <span>{issue.source}</span>
                <span>{issue.status || "unknown"}</span>
                <span>{formatDate(issue.source_created_at)}</span>
                <span>{issue.latest_extraction?.issue_subcategory ? humanize(issue.latest_extraction.issue_subcategory) : "Unclassified"}</span>
              </div>
            </div>
            <button
              type="button"
              className="shrink-0 rounded-md border border-line px-3 py-1 text-xs font-medium text-ink"
              onClick={() => setExpandedIssue(expandedIssue === issue.id ? null : issue.id)}
            >
              {expandedIssue === issue.id ? "Hide" : "Details"}
            </button>
          </div>
          {expandedIssue === issue.id ? <IssueDetails issue={issue} /> : null}
        </article>
      ))}
      {issues.length === 0 ? <div className="rounded-md border border-line bg-white px-4 py-6 text-sm text-slate-500">No issues found</div> : null}
    </div>
  );
}

function IssueDetails({ issue }: { issue: Issue }) {
  const extraction = issue.latest_extraction;
  return (
    <div className="mt-3 grid gap-3 rounded-md bg-panel p-3 text-sm md:grid-cols-2">
      <Field label="Author" value={issue.author_handle || "Unknown"} />
      <Field label="Updated" value={formatDate(issue.source_updated_at)} />
      <Field label="Category" value={extraction ? humanize(extraction.issue_category) : "Not extracted"} />
      <Field label="Subcategory" value={extraction ? humanize(extraction.issue_subcategory) : "Not extracted"} />
      <Field label="Severity" value={extraction?.severity || "Not extracted"} />
      <Field label="Confidence" value={extraction ? `${Math.round(extraction.resolution_confidence * 100)}%` : "Not extracted"} />
      <div className="md:col-span-2">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Original Text</div>
        <p className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap text-slate-700">{issue.original_text || "No body text stored."}</p>
      </div>
      {extraction ? (
        <div className="md:col-span-2">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Resolution Steps</div>
          <p className="mt-1 text-slate-700">
            {extraction.resolution_steps.length > 0 ? extraction.resolution_steps.join("; ") : "No resolution steps detected yet."}
          </p>
        </div>
      ) : null}
    </div>
  );
}

function groupIssues(issues: Issue[], mode: GroupMode) {
  const grouped = new Map<string, Issue[]>();
  for (const issue of issues) {
    const extraction = issue.latest_extraction;
    const keys =
      mode === "category"
        ? [extraction?.issue_category || "triage_needed"]
        : mode === "skill"
          ? extraction?.skills_required.length
            ? extraction.skills_required
            : ["no_skill_detected"]
          : mode === "technology"
            ? extraction?.technologies_involved.length
              ? extraction.technologies_involved
              : ["no_technology_detected"]
            : [issue.source];
    for (const key of keys) {
      grouped.set(key, [...(grouped.get(key) || []), issue]);
    }
  }
  return Array.from(grouped.entries())
    .map(([name, groupedIssues]) => ({
      name,
      issues: groupedIssues,
      subline: mode === "category" ? topSubcategories(groupedIssues) : null
    }))
    .sort((left, right) => right.issues.length - left.issues.length);
}

function topSubcategories(issues: Issue[]) {
  const counts = new Map<string, number>();
  for (const issue of issues) {
    const subcategory = issue.latest_extraction?.issue_subcategory;
    if (subcategory) counts.set(subcategory, (counts.get(subcategory) || 0) + 1);
  }
  return Array.from(counts.entries())
    .sort((left, right) => right[1] - left[1])
    .slice(0, 2)
    .map(([name]) => humanize(name))
    .join(", ");
}

function TabButton({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} className={`px-3 py-2 text-sm font-medium ${active ? "border-b-2 border-accent text-ink" : "text-slate-500"}`}>
      {label}
    </button>
  );
}

function ModeButton({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} className={`rounded-md border px-3 py-2 text-sm font-medium ${active ? "border-accent bg-white text-ink" : "border-line text-slate-600"}`}>
      {label}
    </button>
  );
}

function Select({ label, value, values, onChange }: { label: string; value: string; values: string[]; onChange: (value: string) => void }) {
  return (
    <label className="text-sm text-slate-600">
      <span className="mr-2 font-medium text-ink">{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className="rounded-md border border-line bg-white px-3 py-2">
        {values.map((item) => (
          <option key={item} value={item}>
            {humanize(item)}
          </option>
        ))}
      </select>
    </label>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-slate-700">{value}</div>
    </div>
  );
}

function humanize(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value: string | null) {
  if (!value) return "No date";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}
