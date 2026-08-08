/** @odoo-module **/

const DB_NAME = "ems_scanner";
const STORE = "offline_scans";

function uuid() {
    return crypto.randomUUID();
}

function openDb() {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open(DB_NAME, 1);
        req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: "client_scan_uid" });
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
    });
}

async function addOffline(item) {
    const db = await openDb();
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(item);
    return new Promise((resolve, reject) => {
        tx.oncomplete = resolve;
        tx.onerror = () => reject(tx.error);
    });
}

async function allOffline() {
    const db = await openDb();
    return new Promise((resolve, reject) => {
        const req = db.transaction(STORE, "readonly").objectStore(STORE).getAll();
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
    });
}

async function clearOffline(ids) {
    const db = await openDb();
    const tx = db.transaction(STORE, "readwrite");
    ids.forEach((id) => tx.objectStore(STORE).delete(id));
}

async function jsonRpc(path, params) {
    const response = await fetch(path, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        credentials: "same-origin",
        body: JSON.stringify({jsonrpc: "2.0", method: "call", params, id: uuid()}),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    if (payload.error) throw new Error(payload.error.message || "RPC error");
    return payload.result;
}

document.addEventListener("DOMContentLoaded", () => {
    const state = document.querySelector("#ems-network-state");
    const result = document.querySelector("#ems-scan-result");
    const device = document.querySelector("#ems-device-uid");
    const envelope = document.querySelector("#ems-envelope");

    const refreshState = () => state.textContent = navigator.onLine ? "Online" : "Offline";
    window.addEventListener("online", refreshState);
    window.addEventListener("offline", refreshState);
    refreshState();

    document.querySelector("#ems-submit-scan")?.addEventListener("click", async () => {
        const item = {
            envelope: envelope.value.trim(),
            device_uid: device.value.trim(),
            client_scan_uid: uuid(),
            client_scanned_at: new Date().toISOString(),
        };
        try {
            if (!navigator.onLine) throw new Error("offline");
            const out = await jsonRpc("/ems/api/v1/scan/validate", item);
            result.textContent = JSON.stringify(out, null, 2);
        } catch (err) {
            await addOffline(item);
            result.textContent = "Stored offline for later synchronization.";
        }
    });

    document.querySelector("#ems-sync-scans")?.addEventListener("click", async () => {
        const scans = await allOffline();
        if (!scans.length) {
            result.textContent = "Offline queue is empty.";
            return;
        }
        try {
            const out = await jsonRpc("/ems/api/v1/scan/sync", {
                device_uid: device.value.trim(),
                scans,
            });
            await clearOffline(scans.map((x) => x.client_scan_uid));
            result.textContent = JSON.stringify(out, null, 2);
        } catch (err) {
            result.textContent = `Sync failed: ${err.message}`;
        }
    });

    if ("serviceWorker" in navigator) {
        navigator.serviceWorker.register("/ems/scanner/sw.js").catch(() => {});
    }
});
