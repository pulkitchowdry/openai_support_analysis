"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type OperationSummary = {
  status: string;
  counts: Record<string, number>;
  warnings: string[];
};

export function FetchLatestButton({ apiBaseUrl }: { apiBaseUrl: string }) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [summary, setSummary] = useState<OperationSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function fetchLatest(useCheckpoint = true) {
    setIsLoading(true);
    setError(null);
    setSummary(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/ingestion/fetch-latest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ingest_limit: 100, use_checkpoint: useCheckpoint })
      });
      if (!response.ok) {
        throw new Error(`Fetch failed with HTTP ${response.status}`);
      }
      const data = (await response.json()) as OperationSummary;
      setSummary(data);
      router.refresh();
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "Fetch failed");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-2">
      <div className="flex flex-wrap justify-end gap-2">
        <button
          type="button"
          onClick={() => fetchLatest(true)}
          disabled={isLoading}
          className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? "Fetching..." : "Fetch Latest Data"}
        </button>
        <button
          type="button"
          onClick={() => fetchLatest(false)}
          disabled={isLoading}
          className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink disabled:cursor-not-allowed disabled:opacity-60"
        >
          Backfill Recent History
        </button>
      </div>
      {summary ? (
        <p className="max-w-xl text-right text-xs text-slate-600">
          Inserted {summary.counts.raw_items_inserted ?? 0} raw items, normalized{" "}
          {summary.counts.normalized_issues ?? 0}, extracted {summary.counts.ai_extractions ?? 0}.
        </p>
      ) : null}
      {error ? <p className="max-w-xl text-right text-xs text-red-700">{error}</p> : null}
    </div>
  );
}
