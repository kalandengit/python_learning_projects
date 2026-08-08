/** @odoo-module **/

/**
 * EMS scanner front-end.
 *
 * Everything here is untrusted: the server re-validates the envelope, the
 * device secret and the operator's group on every call. The client's only jobs
 * are capturing codes, queueing them while offline, and replaying the queue.
 */

const DB_NAME = "ems_scanner";
const DB_VERSION = 1;
const STORE = "offline_scans";
const CREDENTIAL_KEY = "ems_scanner_credentials";
const SCAN_COOLDOWN_MS = 2500;

function uuid() {
    return crypto.randomUUID();
}

// ---------------------------------------------------------------- IndexedDB

function openDb() {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open(DB_NAME, DB_VERSION);
        req.onupgradeneeded = () => {
            const db = req.result;
            if (!db.objectStoreNames.contains(STORE)) {
                db.createObjectStore(STORE, { keyPath: "client_scan_uid" });
            }
        };
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
    });
}

function txDone(tx) {
    return new Promise((resolve, reject) => {
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
        tx.onabort = () => reject(tx.error);
    });
}

async function addOffline(item) {
    const db = await openDb();
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(item);
    await txDone(tx);
}

async function allOffline() {
    const db = await openDb();
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).getAll();
    return new Promise((resolve, reject) => {
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
    });
}

async function clearOffline(ids) {
    const db = await openDb();
    const tx = db.transaction(STORE, "readwrite");
    const store = tx.objectStore(STORE);
    ids.forEach((id) => store.delete(id));
    await txDone(tx);
}

async function countOffline() {
    return (await allOffline()).length;
}

// ---------------------------------------------------------------------- RPC

async function jsonRpc(path, params) {
    const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ jsonrpc: "2.0", method: "call", params, id: uuid() }),
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    if (payload.error) {
        const data = payload.error.data || {};
        throw new Error(data.message || payload.error.message || "RPC error");
    }
    return payload.result;
}

// --------------------------------------------------------------- Credentials

function loadCredentials() {
    try {
        return JSON.parse(localStorage.getItem(CREDENTIAL_KEY)) || {};
    } catch {
        return {};
    }
}

function saveCredentials(deviceUid, deviceSecret) {
    localStorage.setItem(
        CREDENTIAL_KEY,
        JSON.stringify({ device_uid: deviceUid, device_secret: deviceSecret })
    );
}

// -------------------------------------------------------------------- Camera

class CameraScanner {
    constructor(video, onCode) {
        this.video = video;
        this.onCode = onCode;
        this.stream = null;
        this.detector = null;
        this.running = false;
        this.lastCode = null;
        this.lastCodeAt = 0;
    }

    static isSupported() {
        return "BarcodeDetector" in window && !!navigator.mediaDevices?.getUserMedia;
    }

    async start() {
        if (this.running) {
            return;
        }
        this.detector = new window.BarcodeDetector({ formats: ["qr_code"] });
        this.stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment" },
            audio: false,
        });
        this.video.srcObject = this.stream;
        this.video.setAttribute("playsinline", "true");
        await this.video.play();
        this.running = true;
        this._tick();
    }

    stop() {
        this.running = false;
        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
            this.stream = null;
        }
        this.video.srcObject = null;
    }

    async _tick() {
        if (!this.running) {
            return;
        }
        try {
            const codes = await this.detector.detect(this.video);
            if (codes.length) {
                const value = codes[0].rawValue;
                const now = Date.now();
                // One physical badge stays in frame for many frames; ignore
                // repeats of the same code inside the cooldown window.
                if (value !== this.lastCode || now - this.lastCodeAt > SCAN_COOLDOWN_MS) {
                    this.lastCode = value;
                    this.lastCodeAt = now;
                    this.onCode(value);
                }
            }
        } catch {
            // A dropped frame is not fatal; keep scanning.
        }
        requestAnimationFrame(() => this._tick());
    }
}

// ----------------------------------------------------------------- Bootstrap

function setup() {
    const els = {
        network: document.querySelector("#ems-network-state"),
        queue: document.querySelector("#ems-queue-state"),
        result: document.querySelector("#ems-scan-result"),
        device: document.querySelector("#ems-device-uid"),
        secret: document.querySelector("#ems-device-secret"),
        envelope: document.querySelector("#ems-envelope"),
        video: document.querySelector("#ems-camera"),
        startCamera: document.querySelector("#ems-start-camera"),
        stopCamera: document.querySelector("#ems-stop-camera"),
        submit: document.querySelector("#ems-submit-scan"),
        sync: document.querySelector("#ems-sync-scans"),
        cameraNote: document.querySelector("#ems-camera-note"),
    };
    if (!els.result) {
        return; // not on the scanner page
    }

    const stored = loadCredentials();
    if (stored.device_uid) {
        els.device.value = stored.device_uid;
    }
    if (stored.device_secret) {
        els.secret.value = stored.device_secret;
    }

    function show(message, level = "info") {
        els.result.textContent =
            typeof message === "string" ? message : JSON.stringify(message, null, 2);
        els.result.dataset.level = level;
    }

    async function refreshQueue() {
        const pending = await countOffline().catch(() => 0);
        els.queue.textContent = pending
            ? `${pending} scan(s) waiting to sync`
            : "Offline queue empty";
        els.sync.disabled = !pending;
    }

    const refreshNetwork = () => {
        els.network.textContent = navigator.onLine ? "Online" : "Offline";
        els.network.className = navigator.onLine ? "text-success" : "text-warning";
    };
    window.addEventListener("online", () => {
        refreshNetwork();
        syncQueue();
    });
    window.addEventListener("offline", refreshNetwork);
    refreshNetwork();

    function credentials() {
        const deviceUid = els.device.value.trim();
        const deviceSecret = els.secret.value.trim();
        saveCredentials(deviceUid, deviceSecret);
        return { device_uid: deviceUid, device_secret: deviceSecret };
    }

    async function submitScan(envelope) {
        if (!envelope) {
            show("Nothing to validate.", "warning");
            return;
        }
        const { device_uid, device_secret } = credentials();
        const item = {
            envelope,
            device_uid,
            client_scan_uid: uuid(),
            client_scanned_at: new Date().toISOString(),
        };
        if (!navigator.onLine) {
            await addOffline(item);
            await refreshQueue();
            show("Offline — stored for later synchronization.", "warning");
            return;
        }
        try {
            const out = await jsonRpc("/ems/scanner/api/scan/validate", { ...item, device_secret });
            show(out, out.result === "accepted" ? "success" : "warning");
        } catch (err) {
            // Only queue transport failures. An authorization refusal will fail
            // again identically, so surface it instead of hiding it in a queue.
            if (navigator.onLine && /^HTTP 4/.test(err.message)) {
                show(`Refused: ${err.message}`, "error");
                return;
            }
            await addOffline(item);
            await refreshQueue();
            show(`Stored offline (${err.message}).`, "warning");
        }
    }

    async function syncQueue() {
        const scans = await allOffline();
        if (!scans.length) {
            await refreshQueue();
            return;
        }
        const { device_uid, device_secret } = credentials();
        try {
            const out = await jsonRpc("/ems/scanner/api/scan/sync", {
                device_uid,
                device_secret,
                scans,
            });
            // Only drop the entries the server actually acknowledged.
            const acknowledged = (out.results || [])
                .filter((row) => row.client_scan_uid)
                .map((row) => row.client_scan_uid);
            await clearOffline(acknowledged);
            await refreshQueue();
            show(out, "success");
        } catch (err) {
            show(`Sync failed: ${err.message}`, "error");
        }
    }

    els.submit?.addEventListener("click", () => submitScan(els.envelope.value.trim()));
    els.sync?.addEventListener("click", syncQueue);

    if (CameraScanner.isSupported()) {
        const camera = new CameraScanner(els.video, (value) => {
            els.envelope.value = value;
            submitScan(value);
        });
        els.startCamera?.addEventListener("click", async () => {
            try {
                await camera.start();
                els.startCamera.disabled = true;
                els.stopCamera.disabled = false;
            } catch (err) {
                show(`Camera unavailable: ${err.message}`, "error");
            }
        });
        els.stopCamera?.addEventListener("click", () => {
            camera.stop();
            els.startCamera.disabled = false;
            els.stopCamera.disabled = true;
        });
    } else {
        els.cameraNote.textContent =
            "This browser has no barcode detector; paste or type the QR payload below.";
        els.startCamera.disabled = true;
        els.stopCamera.disabled = true;
    }

    refreshQueue();

    if ("serviceWorker" in navigator) {
        navigator.serviceWorker.register("/ems/scanner/sw.js").catch(() => {});
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
} else {
    setup();
}
