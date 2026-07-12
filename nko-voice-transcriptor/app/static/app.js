"use strict";

// ---- Tiny API client -------------------------------------------------------
// Token lives in sessionStorage: cleared when the tab closes. (Trade-off vs
// httpOnly cookies documented in SECURITY.md; CSP + no-inline-scripts reduce
// XSS exfiltration risk.)
const TOKEN_KEY = "nko_token";
const getToken = () => sessionStorage.getItem(TOKEN_KEY);
const setToken = (t) => sessionStorage.setItem(TOKEN_KEY, t);
const clearToken = () => sessionStorage.removeItem(TOKEN_KEY);

async function api(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  let payload;
  if (form) {
    payload = form;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const res = await fetch(path, { method, headers, body: payload });
  if (res.status === 401) {
    clearToken();
    showAuth();
    throw new Error("Session expired — please log in again");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch { /* not json */ }
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }
  return res.status === 204 ? null : res.json();
}

// ---- Elements --------------------------------------------------------------
const $ = (id) => document.getElementById(id);
const authPanel = $("auth-panel"), appPanel = $("app-panel");

function showAuth() { authPanel.classList.remove("hidden"); appPanel.classList.add("hidden"); }
function showApp() { authPanel.classList.add("hidden"); appPanel.classList.remove("hidden"); refreshHistory(); }

// ---- Auth ------------------------------------------------------------------
$("auth-form").addEventListener("submit", (e) => e.preventDefault());
for (const btn of document.querySelectorAll("#auth-form button")) {
  btn.addEventListener("click", async (e) => {
    e.preventDefault();
    const mode = e.target.dataset.mode;
    const username = $("username").value.trim();
    const password = $("password").value;
    $("auth-error").textContent = "";
    try {
      if (mode === "register") {
        await api("/api/auth/register", { method: "POST", body: { username, password } });
      }
      const tok = await api("/api/auth/login", { method: "POST", body: { username, password } });
      setToken(tok.access_token);
      showApp();
    } catch (err) {
      $("auth-error").textContent = err.message;
    }
  });
}

// ---- Recording -------------------------------------------------------------
// State machine: idle → recording ⇄ standby(paused) → stop → upload
let recorder = null, chunks = [], timerId = null, elapsedMs = 0, lastTick = 0;
const startBtn = $("start-btn"), standbyBtn = $("standby-btn"), stopBtn = $("stop-btn");

function setRecUI(state) {
  startBtn.disabled = state !== "idle";
  standbyBtn.disabled = state === "idle";
  stopBtn.disabled = state === "idle";
  standbyBtn.textContent = state === "standby" ? "▶ Resume" : "❚❚ Stand by";
  startBtn.classList.toggle("recording", state === "recording");
  $("record-state").textContent =
    state === "recording" ? "recording…" : state === "standby" ? "on stand-by" : "";
}

function tickTimer() {
  const now = Date.now();
  if (recorder && recorder.state === "recording") elapsedMs += now - lastTick;
  lastTick = now;
  $("record-timer").textContent = `${Math.floor(elapsedMs / 1000)}s`;
}

startBtn.addEventListener("click", async () => {
  $("app-error").textContent = "";
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    $("app-error").textContent = "Microphone access denied — you can upload a file instead.";
    return;
  }
  chunks = [];
  elapsedMs = 0;
  lastTick = Date.now();
  recorder = new MediaRecorder(stream);
  recorder.ondataavailable = (e) => chunks.push(e.data);
  recorder.onstop = async () => {
    stream.getTracks().forEach((t) => t.stop());
    clearInterval(timerId);
    $("record-timer").textContent = "";
    setRecUI("idle");
    const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
    await sendAudio(blob, "recording.webm");
  };
  recorder.start();
  setRecUI("recording");
  timerId = setInterval(tickTimer, 250);
});

standbyBtn.addEventListener("click", () => {
  if (!recorder) return;
  if (recorder.state === "recording") {
    recorder.pause();
    setRecUI("standby");
  } else if (recorder.state === "paused") {
    lastTick = Date.now();
    recorder.resume();
    setRecUI("recording");
  }
});

stopBtn.addEventListener("click", () => {
  if (recorder && recorder.state !== "inactive") recorder.stop();
});

$("file-input").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (file) await sendAudio(file, file.name);
  e.target.value = "";
});

async function sendAudio(blob, filename) {
  $("app-error").textContent = "";
  startBtn.disabled = true;
  try {
    const form = new FormData();
    form.append("audio", blob, filename);
    const rec = await api("/api/transcribe", { method: "POST", form });
    $("result").classList.remove("hidden");
    $("result-nko").textContent = rec.text_nko;
    $("result-latin").textContent = rec.text_latin;
    refreshHistory();
  } catch (err) {
    $("app-error").textContent = err.message;
  } finally {
    startBtn.disabled = false;
  }
}

// ---- Copy / paste ------------------------------------------------------------
async function copyToClipboard(btn, text) {
  if (!text) return;
  const original = btn.textContent;
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = "✓ Copied";
  } catch {
    btn.textContent = "✗ Copy blocked";
  }
  setTimeout(() => { btn.textContent = original; }, 1500);
}

$("copy-nko-btn").addEventListener("click", (e) =>
  copyToClipboard(e.target, $("result-nko").textContent));
$("copy-latin-btn").addEventListener("click", (e) =>
  copyToClipboard(e.target, $("result-latin").textContent));
$("copy-text-btn").addEventListener("click", (e) =>
  copyToClipboard(e.target, $("text-output").textContent));

$("paste-btn").addEventListener("click", async () => {
  try {
    const text = await navigator.clipboard.readText();
    if (text) $("text-input").value = text.slice(0, 500);
  } catch {
    $("app-error").textContent =
      "Clipboard read blocked by the browser — paste with Ctrl+V / ⌘V instead.";
  }
});

// ---- Text transliteration --------------------------------------------------
$("text-btn").addEventListener("click", async () => {
  const text = $("text-input").value.trim();
  if (!text) return;
  try {
    const out = await api("/api/transliterate", { method: "POST", body: { text } });
    $("text-output").textContent = out.text_nko;
    $("copy-text-btn").classList.remove("hidden");
  } catch (err) {
    $("app-error").textContent = err.message;
  }
});

// ---- History ---------------------------------------------------------------
async function refreshHistory() {
  try {
    const rows = await api("/api/history?limit=20");
    const ul = $("history");
    ul.replaceChildren();
    for (const row of rows) {
      const li = document.createElement("li");
      const nko = document.createElement("span");
      nko.className = "nko";
      nko.dir = "rtl";
      nko.textContent = row.text_nko;
      const meta = document.createElement("span");
      meta.className = "meta";
      meta.textContent = new Date(row.created_at).toLocaleString();
      const del = document.createElement("button");
      del.className = "secondary";
      del.textContent = "✕";
      del.title = "Delete";
      del.addEventListener("click", async () => {
        await api(`/api/history/${row.id}`, { method: "DELETE" });
        refreshHistory();
      });
      li.append(nko, meta, del);
      ul.append(li);
    }
  } catch { /* history is non-critical; errors surface elsewhere */ }
}

// ---- Boot ------------------------------------------------------------------
if (getToken()) showApp(); else showAuth();
