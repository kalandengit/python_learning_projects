"use strict";

// Tokens live in sessionStorage (cleared when the tab closes; no cookies → no CSRF).
const API = "/api/v1";

const $ = (id) => document.getElementById(id);

let mediaRecorder = null;
let chunks = [];

function authHeaders() {
  const token = sessionStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch(path, options = {}) {
  options.headers = { ...(options.headers || {}), ...authHeaders() };
  let response = await fetch(API + path, options);
  if (response.status === 401 && sessionStorage.getItem("refresh_token")) {
    const ok = await refreshTokens();
    if (ok) {
      options.headers = { ...(options.headers || {}), ...authHeaders() };
      response = await fetch(API + path, options);
    }
  }
  return response;
}

async function refreshTokens() {
  const refresh_token = sessionStorage.getItem("refresh_token");
  const response = await fetch(`${API}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token }),
  });
  if (!response.ok) { clearSession(); return false; }
  storeTokens(await response.json());
  return true;
}

function storeTokens(payload) {
  sessionStorage.setItem("access_token", payload.access_token);
  sessionStorage.setItem("refresh_token", payload.refresh_token);
  updateAuthUi(true);
}

function clearSession() {
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("refresh_token");
  updateAuthUi(false);
}

function updateAuthUi(loggedIn) {
  $("btn-login").classList.toggle("hidden", loggedIn);
  $("btn-logout").classList.toggle("hidden", !loggedIn);
  $("history-panel").classList.toggle("hidden", !loggedIn);
  if (loggedIn) { $("auth-panel").classList.add("hidden"); loadHistory(); }
}

async function submitAuth(register) {
  const email = $("auth-email").value;
  const password = $("auth-password").value;
  const path = register ? "/auth/register" : "/auth/login";
  const response = await fetch(API + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const message = $("auth-message");
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    message.textContent = body.detail || `Error ${response.status}`;
    return;
  }
  if (register) {
    message.textContent = "Account created — log in now.";
  } else {
    storeTokens(await response.json());
    message.textContent = "";
  }
}

async function transcribeBlob(blob, filename) {
  $("status").textContent = "…";
  const form = new FormData();
  form.append("audio", blob, filename);
  form.append("language", $("language").value);
  const engine = $("engine").value;
  if (engine) form.append("asr_engine", engine);
  form.append("store_history", $("store-history").checked ? "true" : "false");
  const response = await apiFetch("/transcriptions/upload", { method: "POST", body: form });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    $("status").textContent = body.detail || `Error ${response.status}`;
    return;
  }
  const data = await response.json();
  $("status").textContent = `${data.asr_engine} · ${data.duration_ms} ms`;
  $("latin-out").textContent = data.latin_text;
  $("nko-out").textContent = data.nko_text;
  $("result").classList.remove("hidden");
  if ($("store-history").checked) loadHistory();
}

async function loadHistory() {
  if (!sessionStorage.getItem("access_token")) return;
  const response = await apiFetch("/transcriptions");
  if (!response.ok) return;
  const rows = await response.json();
  const tbody = $("history-table").querySelector("tbody");
  tbody.replaceChildren();
  for (const row of rows) {
    const tr = document.createElement("tr");
    const tdLatin = document.createElement("td");
    tdLatin.textContent = row.latin_text;
    const tdNko = document.createElement("td");
    tdNko.className = "nko-cell";
    tdNko.textContent = row.nko_text;
    const tdDel = document.createElement("td");
    const del = document.createElement("button");
    del.textContent = "✕";
    del.addEventListener("click", async () => {
      await apiFetch(`/transcriptions/${row.id}`, { method: "DELETE" });
      loadHistory();
    });
    tdDel.appendChild(del);
    tr.append(tdLatin, tdNko, tdDel);
    tbody.appendChild(tr);
  }
}

async function searchLexicon() {
  const q = $("lex-query").value.trim();
  if (!q) return;
  const direction = $("lex-direction").value;
  const response = await fetch(
    `${API}/lexicon/search?q=${encodeURIComponent(q)}&direction=${direction}`
  );
  if (!response.ok) return;
  const data = await response.json();
  const tbody = $("lex-results").querySelector("tbody");
  tbody.replaceChildren();
  for (const row of data.results) {
    const tr = document.createElement("tr");
    const tdFr = document.createElement("td");
    tdFr.textContent = row.fr;
    const tdNko = document.createElement("td");
    tdNko.className = "nko-cell";
    tdNko.textContent = row.nko;
    tr.append(tdFr, tdNko);
    tbody.appendChild(tr);
  }
}

function setupRecording() {
  $("btn-record").addEventListener("click", async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      chunks = [];
      mediaRecorder.addEventListener("dataavailable", (e) => chunks.push(e.data));
      mediaRecorder.addEventListener("stop", () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
        transcribeBlob(blob, "recording.webm");
      });
      mediaRecorder.start();
      $("btn-record").classList.add("recording");
      $("btn-record").disabled = true;
      $("btn-stop").disabled = false;
    } catch (err) {
      $("status").textContent = "Microphone unavailable";
    }
  });
  $("btn-stop").addEventListener("click", () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
    $("btn-record").classList.remove("recording");
    $("btn-record").disabled = false;
    $("btn-stop").disabled = true;
  });
  $("file-input").addEventListener("change", () => {
    const file = $("file-input").files[0];
    if (file) transcribeBlob(file, file.name);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const lang = sessionStorage.getItem("ui-lang") || "en";
  $("ui-lang").value = lang;
  applyI18n(lang);
  $("ui-lang").addEventListener("change", () => applyI18n($("ui-lang").value));

  $("btn-login").addEventListener("click", () => $("auth-panel").classList.toggle("hidden"));
  $("btn-logout").addEventListener("click", async () => {
    await apiFetch("/auth/logout", { method: "POST" });
    clearSession();
  });
  $("auth-form").addEventListener("submit", (e) => { e.preventDefault(); submitAuth(false); });
  $("btn-register").addEventListener("click", () => submitAuth(true));
  $("btn-search").addEventListener("click", searchLexicon);
  $("lex-query").addEventListener("keydown", (e) => { if (e.key === "Enter") searchLexicon(); });

  buildKeyboard($("keyboard"), $("kb-target"));
  setupRecording();
  updateAuthUi(Boolean(sessionStorage.getItem("access_token")));
});
