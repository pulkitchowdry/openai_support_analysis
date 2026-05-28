type Row = {
  name: string;
  count: number;
};

export function DataTable({ title, rows }: { title: string; rows: Row[] }) {
  return (
    <section className="rounded-md border border-line bg-white">
      <header className="border-b border-line px-4 py-3">
        <h2 className="text-sm font-semibold text-ink">{title}</h2>
      </header>
      <div className="divide-y divide-line">
        {rows.map((row) => (
          <div key={row.name} className="flex items-center justify-between px-4 py-3 text-sm">
            <span className="text-slate-700">{row.name}</span>
            <span className="font-medium text-ink">{row.count}</span>
          </div>
        ))}
        {rows.length === 0 ? <div className="px-4 py-6 text-sm text-slate-500">No data yet</div> : null}
      </div>
    </section>
  );
}
