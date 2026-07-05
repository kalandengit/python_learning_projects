import { useEffect, useState } from "react";
import { ticketQrObjectUrl } from "../lib/resources";
import { Spinner } from "./ui";

// Re-fetches the signed QR PNG on an interval so the envelope timestamp stays
// fresh (§2: QR refresh ≤60 s). Only VALID tickets have a scannable QR.
const REFRESH_MS = 55_000;

export function TicketQr({ ticketId, active }: { ticketId: string; active: boolean }) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!active) return;
    let current: string | null = null;
    let cancelled = false;

    async function load() {
      try {
        const next = await ticketQrObjectUrl(ticketId);
        if (cancelled) {
          URL.revokeObjectURL(next);
          return;
        }
        if (current) URL.revokeObjectURL(current);
        current = next;
        setUrl(next);
        setError(false);
      } catch {
        if (!cancelled) setError(true);
      }
    }

    void load();
    const timer = window.setInterval(() => void load(), REFRESH_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
      if (current) URL.revokeObjectURL(current);
    };
  }, [ticketId, active]);

  if (!active) {
    return <p className="text-sm text-slate-500">QR is available only for valid tickets.</p>;
  }
  if (error) {
    return <p className="text-sm text-red-600">Could not load QR code.</p>;
  }
  if (!url) {
    return <Spinner label="Generating QR" />;
  }
  return (
    <img
      src={url}
      width={192}
      height={192}
      alt="Entry QR code — present this at the gate"
      className="h-48 w-48 rounded-lg border border-slate-200 bg-white p-2"
    />
  );
}
