import { useCallback, useEffect, useRef, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";
import { validateBadge, validateTicket } from "../lib/resources";
import { deviceId } from "../lib/device";
import { errorDetail, HTTPError } from "../lib/api";
import {
  allQueuedScans,
  dequeueScan,
  enqueueScan,
  queueSize,
  type QueuedScan,
} from "../lib/offline-queue";
import { Alert, Button, Card, Field, TextInput } from "../components/ui";

type Mode = "ticket" | "badge";

interface ScanFeedback {
  tone: "success" | "error" | "info";
  message: string;
}

const READER_ID = "qr-reader";
const DEDUPE_MS = 3000;

export function ScannerPage() {
  const [mode, setMode] = useState<Mode>("ticket");
  const [zone, setZone] = useState("");
  const [scanning, setScanning] = useState(false);
  const [feedback, setFeedback] = useState<ScanFeedback | null>(null);
  const [online, setOnline] = useState(navigator.onLine);
  const [pending, setPending] = useState(0);

  const scannerRef = useRef<Html5Qrcode | null>(null);
  const lastScanRef = useRef<{ value: string; at: number }>({ value: "", at: 0 });
  // Keep the latest mode/zone available to the scan callback without
  // restarting the camera each time they change.
  const modeRef = useRef(mode);
  modeRef.current = mode;
  const zoneRef = useRef(zone);
  zoneRef.current = zone;

  const refreshPending = useCallback(async () => {
    setPending(await queueSize());
  }, []);

  const submit = useCallback(
    async (kind: Mode, qrData: string, zoneValue: string | null) => {
      const dev = deviceId();
      try {
        if (kind === "ticket") {
          const res = await validateTicket(qrData, dev, zoneValue);
          setFeedback({ tone: "success", message: `Ticket ${res.result} ✓` });
        } else {
          const res = await validateBadge(qrData, dev, zoneValue);
          setFeedback({
            tone: "success",
            message: `${res.holder_name} — ${res.badge_type.replace(/_/g, " ")} ✓`,
          });
        }
      } catch (err) {
        if (err instanceof HTTPError) {
          const status = err.response.status;
          if (status === 409) {
            setFeedback({ tone: "error", message: "Already used — duplicate scan." });
          } else if (status === 429) {
            setFeedback({ tone: "error", message: "Scanning too fast — slow down." });
          } else {
            setFeedback({ tone: "error", message: await errorDetail(err) });
          }
          return; // a real server rejection — do NOT queue it
        }
        // Network failure → queue for later sync.
        await enqueueScan({
          id: crypto.randomUUID(),
          kind,
          qr_data: qrData,
          device_id: dev,
          zone: zoneValue,
          queued_at: Date.now(),
        });
        await refreshPending();
        setFeedback({ tone: "info", message: "Offline — scan queued for sync." });
      }
    },
    [refreshPending],
  );

  const onDecoded = useCallback(
    (decoded: string) => {
      const now = Date.now();
      const last = lastScanRef.current;
      if (decoded === last.value && now - last.at < DEDUPE_MS) return;
      lastScanRef.current = { value: decoded, at: now };
      void submit(modeRef.current, decoded, zoneRef.current || null);
    },
    [submit],
  );

  async function start() {
    setFeedback(null);
    const scanner = new Html5Qrcode(READER_ID, { verbose: false });
    scannerRef.current = scanner;
    try {
      await scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        onDecoded,
        () => {},
      );
      setScanning(true);
    } catch {
      setFeedback({ tone: "error", message: "Could not access the camera." });
      scannerRef.current = null;
    }
  }

  const stop = useCallback(async () => {
    const scanner = scannerRef.current;
    if (scanner) {
      try {
        await scanner.stop();
        scanner.clear();
      } catch {
        /* already stopped */
      }
      scannerRef.current = null;
    }
    setScanning(false);
  }, []);

  const sync = useCallback(async () => {
    if (!navigator.onLine) return;
    const queued: QueuedScan[] = await allQueuedScans();
    for (const scan of queued) {
      try {
        if (scan.kind === "ticket") {
          await validateTicket(scan.qr_data, scan.device_id, scan.zone);
        } else {
          await validateBadge(scan.qr_data, scan.device_id, scan.zone);
        }
        await dequeueScan(scan.id);
      } catch (err) {
        if (err instanceof HTTPError) {
          // Server made a decision (accepted/duplicate/rejected) — drop it.
          await dequeueScan(scan.id);
        } else {
          break; // still offline; stop and retry later
        }
      }
    }
    await refreshPending();
  }, [refreshPending]);

  useEffect(() => {
    void refreshPending();
    function goOnline() {
      setOnline(true);
      void sync();
    }
    function goOffline() {
      setOnline(false);
    }
    window.addEventListener("online", goOnline);
    window.addEventListener("offline", goOffline);
    return () => {
      window.removeEventListener("online", goOnline);
      window.removeEventListener("offline", goOffline);
      void stop();
    };
  }, [refreshPending, sync, stop]);

  return (
    <section aria-labelledby="scanner-heading" className="mx-auto max-w-md space-y-4">
      <h1 id="scanner-heading" className="text-2xl font-bold">
        Entry scanner
      </h1>

      <div className="flex items-center gap-2 text-sm" aria-live="polite">
        <span
          className={`inline-block h-2.5 w-2.5 rounded-full ${online ? "bg-green-500" : "bg-amber-500"}`}
          aria-hidden
        />
        {online ? "Online" : "Offline — scans will queue"}
        {pending > 0 && (
          <span className="ml-auto rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
            {pending} queued
          </span>
        )}
      </div>

      <Card>
        <div className="flex flex-col gap-4">
          <fieldset>
            <legend className="mb-2 text-sm font-medium text-slate-700">Scan mode</legend>
            <div className="flex gap-2">
              {(["ticket", "badge"] as const).map((m) => (
                <label
                  key={m}
                  className={`flex-1 cursor-pointer rounded-lg border px-3 py-2 text-center text-sm capitalize ${
                    mode === m ? "border-brand-500 bg-brand-50 text-brand-700" : "border-slate-300"
                  }`}
                >
                  <input
                    type="radio"
                    name="mode"
                    value={m}
                    checked={mode === m}
                    onChange={() => setMode(m)}
                    className="sr-only"
                  />
                  {m}
                </label>
              ))}
            </div>
          </fieldset>

          <Field label="Zone" hint="Required for badge zone checks; optional for tickets.">
            {({ id, describedBy }) => (
              <TextInput id={id} aria-describedby={describedBy} value={zone} onChange={(e) => setZone(e.target.value)} placeholder="e.g. backstage" />
            )}
          </Field>

          <div id={READER_ID} className="overflow-hidden rounded-lg bg-black" />

          <div className="flex gap-2">
            {!scanning ? (
              <Button onClick={() => void start()} className="flex-1">
                Start camera
              </Button>
            ) : (
              <Button variant="secondary" onClick={() => void stop()} className="flex-1">
                Stop
              </Button>
            )}
            {pending > 0 && online && (
              <Button variant="secondary" onClick={() => void sync()}>
                Sync {pending}
              </Button>
            )}
          </div>
        </div>
      </Card>

      {feedback && (
        <div aria-live="assertive">
          <Alert tone={feedback.tone}>{feedback.message}</Alert>
        </div>
      )}
    </section>
  );
}
