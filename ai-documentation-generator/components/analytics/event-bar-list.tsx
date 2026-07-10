export function EventBarList({ events }: { events: Array<{ eventName: string; count: number }> }) {
  const max = Math.max(...events.map((event) => event.count), 1);
  if (!events.length) return <p className="text-sm text-slate-500">No events captured yet.</p>;
  return (
    <div className="space-y-3">
      {events.map((event) => (
        <div key={event.eventName}>
          <div className="mb-1 flex justify-between text-sm">
            <span className="font-medium">{event.eventName}</span>
            <span className="text-slate-500">{event.count}</span>
          </div>
          <div className="h-2 rounded-full bg-slate-100">
            <div className="h-2 rounded-full bg-slate-900" style={{ width: `${Math.max(6, (event.count / max) * 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}
