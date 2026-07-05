import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createEvent, createTier, publishEvent } from "../lib/resources";
import { errorDetail } from "../lib/api";
import { formatMoney } from "../lib/format";
import { Alert, Button, Card, Field, Spinner, TextInput } from "../components/ui";
import { MapPicker, type LatLng } from "../components/MapPicker";

interface TierDraft {
  name: string;
  price: string; // major units as typed
  capacity: string;
}

const STEPS = ["Details", "Location", "Tickets", "Review"] as const;

export function OrganizerWizardPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [venue, setVenue] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [location, setLocation] = useState<LatLng | null>(null);
  const [radius, setRadius] = useState("");
  const [tiers, setTiers] = useState<TierDraft[]>([{ name: "General", price: "0", capacity: "100" }]);

  function updateTier(i: number, patch: Partial<TierDraft>) {
    setTiers((prev) => prev.map((t, idx) => (idx === i ? { ...t, ...patch } : t)));
  }

  function validateStep(): string | null {
    if (step === 0) {
      if (!title.trim()) return "Title is required.";
      if (!startsAt || !endsAt) return "Start and end times are required.";
      if (new Date(endsAt) <= new Date(startsAt)) return "End must be after start.";
    }
    if (step === 2) {
      if (tiers.length === 0) return "Add at least one ticket tier.";
      for (const t of tiers) {
        if (!t.name.trim()) return "Every tier needs a name.";
        if (Number(t.price) < 0 || Number.isNaN(Number(t.price))) return "Price must be ≥ 0.";
        if (Number(t.capacity) < 1) return "Capacity must be at least 1.";
      }
    }
    return null;
  }

  function next() {
    const err = validateStep();
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  async function publish() {
    setBusy(true);
    setError(null);
    try {
      const event = await createEvent({
        title,
        ...(description ? { description } : {}),
        starts_at: new Date(startsAt).toISOString(),
        ends_at: new Date(endsAt).toISOString(),
        ...(venue ? { venue_name: venue } : {}),
        ...(location ? { latitude: location.lat, longitude: location.lng } : {}),
        ...(location && radius ? { geofence_radius_m: Number(radius) } : {}),
      });
      for (const t of tiers) {
        await createTier(event.id, {
          name: t.name,
          price_cents: Math.round(Number(t.price) * 100),
          capacity: Number(t.capacity),
        });
      }
      await publishEvent(event.id);
      navigate(`/events/${event.id}`);
    } catch (err) {
      setError(await errorDetail(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-2 text-2xl font-bold">Create an event</h1>
      <ol className="mb-6 flex gap-2 text-sm" aria-label="Progress">
        {STEPS.map((label, i) => (
          <li
            key={label}
            aria-current={i === step ? "step" : undefined}
            className={[
              "rounded-full px-3 py-1",
              i === step ? "bg-brand-600 text-white" : i < step ? "bg-brand-100 text-brand-700" : "bg-slate-100 text-slate-500",
            ].join(" ")}
          >
            {i + 1}. {label}
          </li>
        ))}
      </ol>

      <Card>
        {error && (
          <div className="mb-4">
            <Alert>{error}</Alert>
          </div>
        )}

        {step === 0 && (
          <div className="flex flex-col gap-4">
            <Field label="Title">
              {({ id }) => <TextInput id={id} value={title} onChange={(e) => setTitle(e.target.value)} required />}
            </Field>
            <Field label="Description">
              {({ id }) => (
                <textarea
                  id={id}
                  rows={4}
                  className="rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              )}
            </Field>
            <Field label="Venue name">
              {({ id }) => <TextInput id={id} value={venue} onChange={(e) => setVenue(e.target.value)} />}
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Starts at">
                {({ id }) => (
                  <TextInput id={id} type="datetime-local" value={startsAt} onChange={(e) => setStartsAt(e.target.value)} required />
                )}
              </Field>
              <Field label="Ends at">
                {({ id }) => (
                  <TextInput id={id} type="datetime-local" value={endsAt} onChange={(e) => setEndsAt(e.target.value)} required />
                )}
              </Field>
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-4">
            <MapPicker value={location} onChange={setLocation} radiusM={radius ? Number(radius) : null} />
            <Field label="Geofence radius (metres, optional)">
              {({ id }) => (
                <TextInput id={id} type="number" min={0} value={radius} onChange={(e) => setRadius(e.target.value)} className="w-40" />
              )}
            </Field>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            {tiers.map((tier, i) => (
              <div key={i} className="grid gap-3 rounded-lg border border-slate-200 p-3 sm:grid-cols-[1fr_auto_auto_auto]">
                <Field label="Name">
                  {({ id }) => <TextInput id={id} value={tier.name} onChange={(e) => updateTier(i, { name: e.target.value })} />}
                </Field>
                <Field label="Price">
                  {({ id }) => (
                    <TextInput id={id} type="number" min={0} step="0.01" className="w-28" value={tier.price} onChange={(e) => updateTier(i, { price: e.target.value })} />
                  )}
                </Field>
                <Field label="Capacity">
                  {({ id }) => (
                    <TextInput id={id} type="number" min={1} className="w-24" value={tier.capacity} onChange={(e) => updateTier(i, { capacity: e.target.value })} />
                  )}
                </Field>
                <div className="flex items-end">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setTiers((prev) => prev.filter((_, idx) => idx !== i))}
                    disabled={tiers.length === 1}
                    aria-label={`Remove tier ${tier.name || i + 1}`}
                  >
                    Remove
                  </Button>
                </div>
              </div>
            ))}
            <Button type="button" variant="secondary" onClick={() => setTiers((p) => [...p, { name: "", price: "0", capacity: "100" }])}>
              Add tier
            </Button>
          </div>
        )}

        {step === 3 && (
          <dl className="space-y-2 text-sm">
            <Row label="Title" value={title} />
            <Row label="When" value={`${startsAt} → ${endsAt}`} />
            <Row label="Venue" value={venue || "—"} />
            <Row label="Location" value={location ? `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}` : "Not set"} />
            <Row
              label="Tiers"
              value={tiers.map((t) => `${t.name} (${formatMoney(Math.round(Number(t.price) * 100), "eur")}, cap ${t.capacity})`).join("; ")}
            />
            <p className="pt-2 text-slate-500">Publishing makes the event and its tiers publicly visible and purchasable.</p>
          </dl>
        )}

        <div className="mt-6 flex justify-between">
          <Button type="button" variant="secondary" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0 || busy}>
            Back
          </Button>
          {step < STEPS.length - 1 ? (
            <Button type="button" onClick={next}>
              Next
            </Button>
          ) : (
            <Button type="button" onClick={() => void publish()} disabled={busy}>
              {busy ? <Spinner label="Publishing" /> : "Publish event"}
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2">
      <dt className="w-24 font-medium text-slate-500">{label}</dt>
      <dd className="flex-1 text-slate-800">{value}</dd>
    </div>
  );
}
