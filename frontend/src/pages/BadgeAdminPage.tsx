import { useState, type FormEvent } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createBadge, listBadges, listEvents, toggleBadge } from "../lib/resources";
import { errorDetail } from "../lib/api";
import { formatDateTime } from "../lib/format";
import { queryClient } from "../lib/query";
import { Alert, Button, Card, Field, Spinner, TextInput } from "../components/ui";
import type { BadgeType } from "../lib/schemas";

const BADGE_TYPES: BadgeType[] = [
  "MANAGEMENT_TEAM",
  "SECURITY_STAFF",
  "CONTRACTORS",
  "VIP_VISITORS",
  "STANDARD_ATTENDEE",
];

export function BadgeAdminPage() {
  const [eventId, setEventId] = useState("");

  // Convenience picker over published events; organizers can also paste an ID.
  const events = useQuery({ queryKey: ["events", "picker"], queryFn: () => listEvents(undefined, 50) });

  return (
    <section aria-labelledby="badges-heading" className="space-y-6">
      <h1 id="badges-heading" className="text-2xl font-bold">
        Badge administration
      </h1>

      <Card>
        <Field label="Event" hint="Pick a published event, or paste an event ID.">
          {({ id, describedBy }) => (
            <div className="flex flex-col gap-2">
              <select
                id={id}
                aria-describedby={describedBy}
                className="rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                value={eventId}
                onChange={(e) => setEventId(e.target.value)}
              >
                <option value="">— select an event —</option>
                {events.data?.items.map((ev) => (
                  <option key={ev.id} value={ev.id}>
                    {ev.title}
                  </option>
                ))}
              </select>
              <TextInput
                aria-label="Event ID"
                placeholder="or paste event ID"
                value={eventId}
                onChange={(e) => setEventId(e.target.value)}
              />
            </div>
          )}
        </Field>
      </Card>

      {eventId && (
        <>
          <IssueBadgeForm eventId={eventId} />
          <BadgeList eventId={eventId} />
        </>
      )}
    </section>
  );
}

function IssueBadgeForm({ eventId }: { eventId: string }) {
  const [holder, setHolder] = useState("");
  const [type, setType] = useState<BadgeType>("SECURITY_STAFF");
  const [zones, setZones] = useState("");
  const [validFrom, setValidFrom] = useState("");
  const [validUntil, setValidUntil] = useState("");
  const [error, setError] = useState<string | null>(null);

  const issue = useMutation({
    mutationFn: () =>
      createBadge({
        event_id: eventId,
        holder_name: holder,
        type,
        access_zones: zones
          .split(",")
          .map((z) => z.trim())
          .filter(Boolean),
        valid_from: new Date(validFrom).toISOString(),
        valid_until: new Date(validUntil).toISOString(),
      }),
    onSuccess: () => {
      setHolder("");
      setZones("");
      void queryClient.invalidateQueries({ queryKey: ["badges", eventId] });
    },
    onError: async (err) => setError(await errorDetail(err)),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!holder.trim() || !validFrom || !validUntil) {
      setError("Holder name and validity window are required.");
      return;
    }
    if (new Date(validUntil) <= new Date(validFrom)) {
      setError("Valid-until must be after valid-from.");
      return;
    }
    issue.mutate();
  }

  return (
    <Card>
      <h2 className="mb-4 text-lg font-semibold">Issue a badge</h2>
      {error && (
        <div className="mb-4">
          <Alert>{error}</Alert>
        </div>
      )}
      <form onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-2">
        <Field label="Holder name">
          {({ id }) => <TextInput id={id} value={holder} onChange={(e) => setHolder(e.target.value)} required />}
        </Field>
        <Field label="Badge type">
          {({ id }) => (
            <select
              id={id}
              className="rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
              value={type}
              onChange={(e) => setType(e.target.value as BadgeType)}
            >
              {BADGE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          )}
        </Field>
        <Field
          label="Access zones"
          hint={type === "MANAGEMENT_TEAM" ? "Management team has all-access; zones optional." : "Comma-separated, e.g. backstage, vip"}
        >
          {({ id, describedBy }) => (
            <TextInput id={id} aria-describedby={describedBy} value={zones} onChange={(e) => setZones(e.target.value)} className="sm:col-span-2" />
          )}
        </Field>
        <Field label="Valid from">
          {({ id }) => <TextInput id={id} type="datetime-local" value={validFrom} onChange={(e) => setValidFrom(e.target.value)} required />}
        </Field>
        <Field label="Valid until">
          {({ id }) => <TextInput id={id} type="datetime-local" value={validUntil} onChange={(e) => setValidUntil(e.target.value)} required />}
        </Field>
        <div className="sm:col-span-2">
          <Button type="submit" disabled={issue.isPending}>
            {issue.isPending ? <Spinner label="Issuing" /> : "Issue badge"}
          </Button>
        </div>
      </form>
    </Card>
  );
}

function BadgeList({ eventId }: { eventId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["badges", eventId],
    queryFn: () => listBadges(eventId),
  });

  const toggle = useMutation({
    mutationFn: (badgeId: string) => toggleBadge(badgeId),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["badges", eventId] }),
  });

  if (isLoading) return <Spinner label="Loading badges" />;
  if (error) return <Alert>Could not load badges (is this your organization's event?).</Alert>;

  const badges = data ?? [];

  return (
    <Card>
      <h2 className="mb-4 text-lg font-semibold">Issued badges ({badges.length})</h2>
      {badges.length === 0 ? (
        <p className="text-slate-500">No badges issued for this event yet.</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500">
              <th scope="col" className="py-2">Holder</th>
              <th scope="col" className="py-2">Type</th>
              <th scope="col" className="py-2">Zones</th>
              <th scope="col" className="py-2">Valid until</th>
              <th scope="col" className="py-2">Status</th>
              <th scope="col" className="py-2 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {badges.map((b) => (
              <tr key={b.id} className="border-b border-slate-100">
                <td className="py-2 font-medium">{b.holder_name}</td>
                <td className="py-2">{b.type.replace(/_/g, " ")}</td>
                <td className="py-2 text-slate-500">{b.access_zones.join(", ") || "—"}</td>
                <td className="py-2 text-slate-500">{formatDateTime(b.valid_until)}</td>
                <td className="py-2">
                  <span className={b.is_active ? "text-green-700" : "text-slate-400"}>
                    {b.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="py-2 text-right">
                  <Button
                    variant="secondary"
                    onClick={() => toggle.mutate(b.id)}
                    disabled={toggle.isPending}
                  >
                    {b.is_active ? "Deactivate" : "Activate"}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}
