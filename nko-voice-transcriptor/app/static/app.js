"use strict";

// ---- Tiny API client -------------------------------------------------------
// Token lives in sessionStorage: cleared when the tab closes. (Trade-off vs
// httpOnly cookies documented in SECURITY.md; CSP + no-inline-scripts reduce
// XSS exfiltration risk.)
const TOKEN_KEY = "nko_token";
const getToken = () => window.NkoSecureStore?.getToken?.() || sessionStorage.getItem(TOKEN_KEY);
const setToken = (t) => {
  sessionStorage.setItem(TOKEN_KEY, t);
  window.NkoSecureStore?.setToken?.(t);
};
const clearToken = () => {
  sessionStorage.removeItem(TOKEN_KEY);
  window.NkoSecureStore?.clear?.();
};

async function api(path, { method = "GET", body, form, retry = true } = {}) {
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
  const res = await fetch(path, { method, headers, body: payload, credentials: "same-origin" });
  if (res.status === 401 && retry && path !== "/api/auth/refresh") {
    const refreshed = await fetch("/api/auth/refresh", {
      method: "POST", credentials: "same-origin",
    });
    if (refreshed.ok) {
      setToken((await refreshed.json()).access_token);
      return api(path, { method, body, form, retry: false });
    }
  }
  if (res.status === 401) {
    clearToken();
    showAuth();
    throw new Error(window.NKO_I18N.t("session_expired"));
  }
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch { /* not json */ }
    throw new Error(typeof detail === "string" ? detail : window.NKO_I18N.t("request_failed"));
  }
  return res.status === 204 ? null : res.json();
}

// ---- Elements --------------------------------------------------------------
const $ = (id) => document.getElementById(id);
const authPanel = $("auth-panel"), appPanel = $("app-panel");

function showAuth() { authPanel.classList.remove("hidden"); appPanel.classList.add("hidden"); }
function showApp() {
  authPanel.classList.add("hidden");
  appPanel.classList.remove("hidden");
  loadLanguages();
  refreshHistory();
  refreshRuntimeState();
}

async function refreshRuntimeState() {
  $("network-state").textContent = navigator.onLine ? "Online" : "Offline";
  try {
    const health = await api("/api/health");
    $("provider-state").textContent = `Provider: ${health.asr_engine} (${health.model_version})`;
  } catch { $("provider-state").textContent = "Backend unavailable"; }
}
window.addEventListener("online", refreshRuntimeState);
window.addEventListener("offline", refreshRuntimeState);

$("logout-btn").addEventListener("click", async () => {
  try { await api("/api/auth/logout", { method: "POST", retry: false }); } catch { /* local logout */ }
  clearToken();
  currentResultId = null;
  $("result").classList.add("hidden");
  showAuth();
  $("username").focus();
});

// ---- Source languages --------------------------------------------------------
let languagesLoaded = false;
async function loadLanguages() {
  if (languagesLoaded) return;
  try {
    const langs = await api("/api/languages");
    const sel = $("language-select");
    sel.replaceChildren();
    for (const lang of langs) {
      const opt = document.createElement("option");
      opt.value = lang.code;
      opt.textContent = lang.name;
      if (lang.default) opt.selected = true;
      sel.append(opt);
    }
    languagesLoaded = true;
  } catch { /* dropdown stays empty; server default applies */ }
}

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
let pendingAudio = null, pendingName = "recording.webm", decodedAudio = null, previewURL = null;
const startBtn = $("start-btn"), standbyBtn = $("standby-btn"), stopBtn = $("stop-btn");

function setRecUI(state) {
  const T = window.NKO_I18N.t;
  startBtn.disabled = state !== "idle";
  standbyBtn.disabled = state === "idle";
  stopBtn.disabled = state === "idle";
  standbyBtn.textContent = state === "standby" ? T("resume") : T("standby");
  startBtn.classList.toggle("recording", state === "recording");
  $("record-state").textContent =
    state === "recording" ? T("recording") : state === "standby" ? T("on_standby") : "";
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
    $("app-error").textContent = window.NKO_I18N.t("microphone_denied");
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
    await preparePreview(blob, "recording.webm");
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
  if (file) await preparePreview(file, file.name);
  e.target.value = "";
});

// The transcription record currently loaded in the editor (null = unsaved text)
let currentResultId = null;

async function loadResult(rec) {
  currentResultId = rec.id ?? null;
  $("result").classList.remove("hidden");
  $("result-nko").value = rec.text_nko;
  $("result-nko").readOnly = true;
  $("result-latin").textContent = rec.text_latin ?? "";
  $("save-nko-btn").disabled = true;   // nothing edited yet
  $("save-state").textContent = "";
  if (currentResultId !== null) await loadSegments(currentResultId);
}

async function loadSegments(transcriptionId) {
  const container = $("segments");
  container.replaceChildren();
  const segments = await api(`/api/history/${transcriptionId}/segments`);
  for (const segment of segments) {
    const card = document.createElement("div");
    card.className = "segment";
    const time = document.createElement("button");
    time.className = "secondary";
    time.textContent = `▶ ${(segment.start_ms / 1000).toFixed(1)}–${(segment.end_ms / 1000).toFixed(1)}s`;
    time.addEventListener("click", () => {
      const player = $("preview-player");
      if (!player.src) return;
      player.currentTime = segment.start_ms / 1000;
      player.play();
      setTimeout(() => player.pause(), Math.max(0, segment.end_ms - segment.start_ms));
    });
    const latin = document.createElement("textarea");
    latin.value = segment.text_latin; latin.rows = 2; latin.lang = "bm";
    const nko = document.createElement("textarea");
    nko.value = segment.text_nko; nko.rows = 2; nko.lang = "nqo"; nko.dir = "rtl";
    const save = document.createElement("button");
    save.className = "secondary"; save.textContent = "Save segment";
    save.addEventListener("click", async () => {
      await api(`/api/history/${transcriptionId}/segments/${segment.id}`, {
        method: "PATCH", body: { text_latin: latin.value, text_nko: nko.value },
      });
      save.textContent = "Saved";
    });
    card.append(time, latin, nko, save);
    container.append(card);
  }
}

async function authenticatedDownload(path, filename) {
  const response = await fetch(path, {
    headers: { Authorization: `Bearer ${getToken()}` }, credentials: "same-origin",
  });
  if (!response.ok) throw new Error("Download failed");
  downloadBlob(filename, await response.blob());
}

$("edit-nko-btn").addEventListener("click", () => {
  $("result-nko").readOnly = false;
  $("result-latin").contentEditable = "true";
  $("result-nko").focus();
  $("save-state").textContent = window.NKO_I18N.t("editing");
});

$("delete-account-btn").addEventListener("click", async () => {
  const password = prompt("Confirm your password to permanently delete the account and data:");
  if (!password) return;
  if (!confirm("This permanently deletes your account, history and contributed audio.")) return;
  await api("/api/auth/account", { method: "DELETE", body: { password } });
  clearToken(); showAuth();
});

async function preparePreview(blob, filename) {
  pendingAudio = blob;
  pendingName = filename;
  if (previewURL) URL.revokeObjectURL(previewURL);
  previewURL = URL.createObjectURL(blob);
  $("preview-player").src = previewURL;
  $("audio-preview").classList.remove("hidden");
  try {
    const context = new AudioContext();
    decodedAudio = await context.decodeAudioData(await blob.arrayBuffer());
    $("trim-start").value = "0";
    $("trim-end").value = decodedAudio.duration.toFixed(1);
    $("trim-end").max = decodedAudio.duration.toFixed(1);
    drawWaveform(decodedAudio);
    await context.close();
  } catch {
    decodedAudio = null; // FFmpeg on the backend may still support the selected video.
    $("trim-end").value = "";
  }
}

function drawWaveform(buffer) {
  const canvas = $("waveform"), ctx = canvas.getContext("2d");
  const data = buffer.getChannelData(0), step = Math.max(1, Math.floor(data.length / canvas.width));
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#168b77";
  ctx.beginPath();
  for (let x = 0; x < canvas.width; x += 1) {
    let peak = 0;
    for (let i = x * step; i < Math.min(data.length, (x + 1) * step); i += 1) {
      peak = Math.max(peak, Math.abs(data[i]));
    }
    ctx.moveTo(x, canvas.height / 2 - peak * canvas.height / 2);
    ctx.lineTo(x, canvas.height / 2 + peak * canvas.height / 2);
  }
  ctx.stroke();
}

function encodeTrimmedWav(buffer, startSeconds, endSeconds) {
  const rate = buffer.sampleRate;
  const start = Math.max(0, Math.floor(startSeconds * rate));
  const end = Math.min(buffer.length, Math.ceil(endSeconds * rate));
  const count = Math.max(0, end - start), bytes = new ArrayBuffer(44 + count * 2);
  const view = new DataView(bytes), channel = buffer.getChannelData(0);
  const text = (offset, value) => [...value].forEach((c, i) => view.setUint8(offset + i, c.charCodeAt(0)));
  text(0, "RIFF"); view.setUint32(4, 36 + count * 2, true); text(8, "WAVE");
  text(12, "fmt "); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
  view.setUint16(22, 1, true); view.setUint32(24, rate, true); view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true); view.setUint16(34, 16, true); text(36, "data");
  view.setUint32(40, count * 2, true);
  for (let i = 0; i < count; i += 1) {
    const sample = Math.max(-1, Math.min(1, channel[start + i]));
    view.setInt16(44 + i * 2, sample < 0 ? sample * 32768 : sample * 32767, true);
  }
  return new Blob([bytes], { type: "audio/wav" });
}

async function submitAudioJob() {
  if (!pendingAudio) return;
  $("app-error").textContent = "";
  startBtn.disabled = true;
  try {
    let blob = pendingAudio, filename = pendingName;
    if (decodedAudio && $("trim-end").value) {
      const start = Number($("trim-start").value), end = Number($("trim-end").value);
      if (!(end > start)) throw new Error("Trim end must be after trim start");
      blob = encodeTrimmedWav(decodedAudio, start, end);
      filename = "trimmed-recording.wav";
    }
    const form = new FormData();
    form.append("audio", blob, filename);
    const lang = $("language-select").value;
    if (lang) form.append("language", lang);
    form.append("training_consent", $("training-consent").checked ? "true" : "false");
    const job = await api("/api/jobs/transcribe", { method: "POST", form });
    $("job-progress").classList.remove("hidden");
    let state = job;
    while (!["completed", "failed"].includes(state.status)) {
      $("job-progress").value = state.progress;
      $("job-state").textContent = `${state.provider}: ${state.status} ${state.progress}%`;
      await new Promise((resolve) => setTimeout(resolve, 800));
      state = await api(`/api/jobs/${job.id}`);
    }
    if (state.status === "failed") throw new Error(state.error || "Transcription failed");
    $("job-progress").value = 100;
    const rec = await api(`/api/jobs/${job.id}/result`);
    loadResult(rec);
    refreshHistory();
    $("audio-preview").classList.add("hidden");
    pendingAudio = null;
  } catch (err) {
    $("app-error").textContent = err.message;
  } finally {
    startBtn.disabled = false;
  }
}

$("submit-audio-btn").addEventListener("click", submitAudioJob);
$("discard-audio-btn").addEventListener("click", () => {
  pendingAudio = null; decodedAudio = null;
  $("preview-player").removeAttribute("src");
  $("audio-preview").classList.add("hidden");
});

// ---- Editing the generated text ---------------------------------------------
$("result-nko").addEventListener("input", () => {
  $("save-nko-btn").disabled = currentResultId === null;
  $("save-state").textContent = window.NKO_I18N.t("unsaved");
});

$("save-nko-btn").addEventListener("click", async () => {
  if (currentResultId === null) return;
  try {
    await api(`/api/history/${currentResultId}`, {
      method: "PATCH",
      body: {
        text_nko: $("result-nko").value,
        text_latin: $("result-latin").textContent,
        submit_for_training: $("submit-correction").checked,
      },
    });
    $("save-nko-btn").disabled = true;
    $("save-state").textContent = window.NKO_I18N.t("saved");
    $("result-nko").readOnly = true;
    $("result-latin").contentEditable = "false";
    refreshHistory();
  } catch (err) {
    $("save-state").textContent = err.message;
  }
});

// ---- Copy / paste ------------------------------------------------------------
async function copyToClipboard(btn, text) {
  if (!text) return;
  const original = btn.textContent;
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = window.NKO_I18N.t("copied");
  } catch {
    btn.textContent = window.NKO_I18N.t("copy_blocked");
  }
  setTimeout(() => { btn.textContent = original; }, 1500);
}

$("copy-nko-btn").addEventListener("click", (e) =>
  copyToClipboard(e.target, $("result-nko").value));
$("copy-latin-btn").addEventListener("click", (e) =>
  copyToClipboard(e.target, $("result-latin").textContent));
$("copy-text-btn").addEventListener("click", (e) =>
  copyToClipboard(e.target, $("text-output").value));

$("share-btn").addEventListener("click", async () => {
  const nko = $("result-nko").value;
  const latin = $("result-latin").textContent;
  if (!nko && !latin) return;
  const text = `N'Ko:\n${nko}\n\nLatin (Manding):\n${latin}`;
  if (window.NkoAndroid?.share) {
    window.NkoAndroid.share(text);
  } else if (navigator.share) {
    try { await navigator.share({ title: "N'Ko transcript", text }); } catch { /* cancelled */ }
  } else {
    await navigator.clipboard.writeText(text);
    $("save-state").textContent = window.NKO_I18N.t("share_copied");
  }
});

$("paste-btn").addEventListener("click", async () => {
  try {
    const text = await navigator.clipboard.readText();
    if (text) $("text-input").value = text.slice(0, 500);
  } catch {
    $("app-error").textContent = window.NKO_I18N.t("clipboard_denied");
  }
});

// ---- Text transliteration --------------------------------------------------
$("text-btn").addEventListener("click", async () => {
  const text = $("text-input").value.trim();
  if (!text) return;
  try {
    const out = await api("/api/transliterate", { method: "POST", body: { text } });
    $("text-output").value = out.text_nko;
    $("copy-text-btn").classList.remove("hidden");
  } catch (err) {
    $("app-error").textContent = err.message;
  }
});

// ---- Download (TXT / PNG / PDF) ---------------------------------------------
// Inspired by transcription/keyboard tools (Google Input Tools, online N'Ko
// editors): let the user take the generated text away in a portable format.
function currentTexts() {
  return { nko: $("result-nko").value, latin: $("result-latin").textContent };
}

function downloadBlob(filename, blob) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function stamp() {
  return new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
}

$("dl-txt-btn").addEventListener("click", () => {
  const { nko, latin } = currentTexts();
  if (!nko) return;
  const body = `N'Ko:\n${nko}\n\nLatin (Manding):\n${latin}\n`;
  downloadBlob(`nko-${stamp()}.txt`, new Blob([body], { type: "text/plain;charset=utf-8" }));
});

$("dl-png-btn").addEventListener("click", () => {
  const { nko, latin } = currentTexts();
  if (!nko) return;
  renderPng(nko, latin);
});

function renderPng(nko, latin) {
  const scale = 2;                 // crisp on hi-dpi
  const pad = 40, fontPx = 54, latinPx = 24, lineH = fontPx * 1.6;
  const maxW = 900;
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  ctx.font = `${fontPx}px "Noto Sans NKo","Ebrima","Kigelia",sans-serif`;
  ctx.direction = "rtl";
  // Word-wrap the N'Ko text to fit maxW.
  const words = nko.split(/\s+/).filter(Boolean);
  const lines = [];
  let line = "";
  for (const w of words) {
    const trial = line ? `${line} ${w}` : w;
    if (ctx.measureText(trial).width > maxW - 2 * pad && line) {
      lines.push(line);
      line = w;
    } else {
      line = trial;
    }
  }
  if (line) lines.push(line);
  if (!lines.length) lines.push(nko);

  const height = pad * 2 + lines.length * lineH + (latin ? latinPx + 20 : 0);
  canvas.width = maxW * scale;
  canvas.height = height * scale;
  ctx.scale(scale, scale);
  // Background
  ctx.fillStyle = "#fbf7ee";
  ctx.fillRect(0, 0, maxW, height);
  // N'Ko lines, right-aligned RTL
  ctx.fillStyle = "#1c2128";
  ctx.font = `${fontPx}px "Noto Sans NKo","Ebrima","Kigelia",sans-serif`;
  ctx.direction = "rtl";
  ctx.textAlign = "right";
  ctx.textBaseline = "top";
  lines.forEach((l, i) => ctx.fillText(l, maxW - pad, pad + i * lineH));
  // Latin caption, left-aligned
  if (latin) {
    ctx.fillStyle = "#5a646e";
    ctx.direction = "ltr";
    ctx.textAlign = "left";
    ctx.font = `${latinPx}px system-ui,sans-serif`;
    ctx.fillText(latin, pad, pad + lines.length * lineH);
  }
  canvas.toBlob((blob) => {
    if (blob) downloadBlob(`nko-${stamp()}.png`, blob);
  }, "image/png");
}

$("dl-pdf-btn").addEventListener("click", () => {
  const { nko, latin } = currentTexts();
  if (!nko) return;
  // Portable, dependency-free PDF: populate a print-only area and open the
  // browser's print dialog, where the user chooses "Save as PDF". Uses the
  // system N'Ko font so glyphs render without embedding.
  $("print-nko").textContent = nko;
  $("print-latin").textContent = latin;
  window.print();
});

// ---- On-screen N'Ko keyboard ------------------------------------------------
// Layout by Unicode. Rows: vowels, consonants, marks/digits, controls.
// Editable N'Ko fields the keyboard can type into:
const NKO_FIELDS = ["result-nko", "text-output", "text-input", "practice-input"];
let activeField = $("text-output");
for (const id of NKO_FIELDS) {
  $(id).addEventListener("focus", (e) => { activeField = e.target; });
}

// Full N'Ko block coverage (U+07C0–U+07FF). See docs/NKO_UNICODE_BLOCK.md.
const KEY_ROWS = [
  // vowels: a ee i e u oo o
  ["ߊ", "ߋ", "ߌ", "ߍ", "ߎ", "ߏ", "ߐ"],
  // consonants
  ["ߓ", "ߔ", "ߕ", "ߖ", "ߗ", "ߘ", "ߙ", "ߚ", "ߛ", "ߜ"],
  ["ߝ", "ߞ", "ߟ", "ߡ", "ߢ", "ߣ", "ߤ", "ߥ", "ߦ", "ߒ"],
  // less common / archaic letters: na woloso, nya woloso, jona ja/cha/ra,
  // dagbasinna
  ["ߠ", "ߧ", "ߨ", "ߩ", "ߪ", "ߑ"],
  // combining tone marks (◌ = dotted-circle placeholder) — short high, low,
  // rising; long descending, high, low, rising. These carry the tone/length
  // that Latin ASR cannot supply, so they are typed by hand.
  ["◌߫", "◌߬", "◌߭", "◌߮", "◌߯", "◌߰", "◌߱"],
  // nasalization, double-dot, dantayalan (combining)
  ["◌߲", "◌߳", "◌߽"],
  // digits ߀–߉
  ["߀", "߁", "߂", "߃", "߄", "߅", "߆", "߇", "߈", "߉"],
  // apostrophes, symbols and punctuation
  ["ߴ", "ߵ", "ߺ", "߶", "߷", "߸", "߹", "؟"],
];
// Special control keys, each: [label, action]
const CONTROL_KEYS = [
  ["␣ space", "space"],
  ["⌫", "backspace"],
];

function insertIntoField(field, text) {
  const start = field.selectionStart ?? field.value.length;
  const end = field.selectionEnd ?? field.value.length;
  field.setRangeText(text, start, end, "end");
  field.dispatchEvent(new Event("input", { bubbles: true }));
}

function backspaceField(field) {
  const start = field.selectionStart ?? field.value.length;
  const end = field.selectionEnd ?? field.value.length;
  if (start === end && start > 0) {
    field.setRangeText("", start - 1, end, "end");
  } else {
    field.setRangeText("", start, end, "end");
  }
  field.dispatchEvent(new Event("input", { bubbles: true }));
}

function keyPress(char) {
  const field = NKO_FIELDS.includes(activeField?.id) ? activeField : $("text-output");
  field.focus();
  // combining marks are shown with a leading dotted circle placeholder
  insertIntoField(field, char.replace("◌", ""));
}

// Char → "latin · Name" tooltip, loaded once from /api/alphabet so the
// keyboard doubles as an alphabet learning aid.
let alphabetMap = null;
async function loadAlphabet() {
  if (alphabetMap) return alphabetMap;
  alphabetMap = {};
  try {
    const rows = await api("/api/alphabet");
    for (const r of rows) {
      alphabetMap[r.char] = r.latin ? `${r.latin} · ${r.name}` : r.name;
    }
  } catch { /* tooltips are optional */ }
  return alphabetMap;
}

function keyTitle(key) {
  const ch = key.replace("◌", "");
  return (alphabetMap && alphabetMap[ch]) || "";
}

function buildKeyboard() {
  const kb = $("keyboard");
  if (kb.childElementCount) return;
  for (const row of KEY_ROWS) {
    const div = document.createElement("div");
    div.className = "kb-row";
    for (const key of row) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "kb-key";
      b.textContent = key;
      b.title = keyTitle(key);       // e.g. "b · Ba", "ɲ · Nya"
      // Don't steal focus from the target field on mousedown.
      b.addEventListener("mousedown", (e) => e.preventDefault());
      b.addEventListener("click", () => keyPress(key));
      div.append(b);
    }
    kb.append(div);
  }
  const ctrl = document.createElement("div");
  ctrl.className = "kb-row";
  for (const [label, action] of CONTROL_KEYS) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "kb-key kb-ctrl";
    b.textContent = label;
    b.addEventListener("mousedown", (e) => e.preventDefault());
    b.addEventListener("click", () => {
      const field = NKO_FIELDS.includes(activeField?.id) ? activeField : $("text-output");
      field.focus();
      if (action === "space") insertIntoField(field, " ");
      else if (action === "backspace") backspaceField(field);
    });
    ctrl.append(b);
  }
  kb.append(ctrl);
}

$("keyboard-toggle").addEventListener("click", async () => {
  await loadAlphabet();
  buildKeyboard();
  const kb = $("keyboard");
  const shown = kb.classList.toggle("hidden") === false;
  $("keyboard-toggle").setAttribute("aria-expanded", String(shown));
});

// ---- Self-evaluation dictation practice -------------------------------------
let practiceItems = [], practiceIndex = -1;

async function nextPractice() {
  if (!practiceItems.length || practiceIndex >= practiceItems.length - 1) {
    practiceItems = await api("/api/dictionary/practice?limit=10");
    practiceIndex = -1;
  }
  practiceIndex += 1;
  $("practice-input").value = "";
  $("practice-feedback").textContent = "";
  $("practice-input").focus();
}

$("dl-vtt-nko").addEventListener("click", () => currentResultId !== null &&
  authenticatedDownload(`/api/history/${currentResultId}/subtitles?format=vtt&script=nko`, `nko-${currentResultId}.vtt`));
$("dl-srt-nko").addEventListener("click", () => currentResultId !== null &&
  authenticatedDownload(`/api/history/${currentResultId}/subtitles?format=srt&script=nko`, `nko-${currentResultId}.srt`));
$("export-history-btn").addEventListener("click", () =>
  authenticatedDownload("/api/history/export.csv", "nko-history.csv"));

function speakPractice() {
  const item = practiceItems[practiceIndex];
  if (!item || !("speechSynthesis" in window)) return;
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(item.fr);
  utterance.lang = "fr-FR";
  speechSynthesis.speak(utterance);
}

$("practice-new").addEventListener("click", () => nextPractice().catch((e) => {
  $("practice-feedback").textContent = e.message;
}));
$("practice-listen").addEventListener("click", speakPractice);
$("practice-check").addEventListener("click", () => {
  const item = practiceItems[practiceIndex];
  if (!item) return;
  const normalize = (value) => value.normalize("NFC").replace(/\s+/g, "").trim();
  const correct = normalize($("practice-input").value) === normalize(item.nko);
  $("practice-feedback").textContent = correct
    ? window.NKO_I18N.t("correct")
    : `${window.NKO_I18N.t("try_again")} ${item.nko}`;
});

// ---- Dictionary lookup ------------------------------------------------------
// French ↔ N'Ko lexicon search. Clicking a result inserts its N'Ko into the
// active N'Ko field, so the dictionary doubles as a spelling aid for editing.
async function runDictionary() {
  const q = $("dict-input").value.trim();
  const dir = $("dict-dir").value;
  const ul = $("dict-results");
  ul.replaceChildren();
  $("dict-empty").classList.add("hidden");
  if (!q) return;
  let res;
  try {
    res = await api(`/api/dictionary?q=${encodeURIComponent(q)}&dir=${dir}&limit=25`);
  } catch (err) {
    $("app-error").textContent = err.message;
    return;
  }
  if (!res.entries.length) {
    $("dict-empty").classList.remove("hidden");
    return;
  }
  for (const e of res.entries) {
    const li = document.createElement("li");
    const fr = document.createElement("span");
    fr.className = "dict-fr";
    fr.textContent = e.cat ? `${e.fr}` : e.fr;
    const nko = document.createElement("span");
    nko.className = "dict-nko nko";
    nko.dir = "rtl";
    nko.textContent = e.nko;
    const insert = document.createElement("button");
    insert.className = "secondary";
    insert.textContent = "→ ߒߞߏ";
    insert.title = "Insert N'Ko";
    insert.addEventListener("click", () => {
      const field = NKO_FIELDS.includes(activeField?.id) ? activeField : $("text-output");
      field.focus();
      insertIntoField(field, e.nko);
    });
    li.append(fr, nko, insert);
    ul.append(li);
  }
}
$("dict-btn").addEventListener("click", runDictionary);
$("dict-input").addEventListener("keydown", (e) => { if (e.key === "Enter") runDictionary(); });
$("dict-dir").addEventListener("change", () => { if ($("dict-input").value.trim()) runDictionary(); });

// ---- History management -----------------------------------------------------
const HISTORY_PAGE = 10;
let historyOffset = 0;
let historyQuery = "";

function renderHistoryRow(row) {
  const li = document.createElement("li");
  const nko = document.createElement("span");
  nko.className = "nko";
  nko.dir = "rtl";
  nko.textContent = row.text_nko;
  const meta = document.createElement("span");
  meta.className = "meta";
  meta.textContent = `${row.language} · ${new Date(row.created_at).toLocaleString()}`;
  const edit = document.createElement("button");
  edit.className = "secondary";
  edit.textContent = "✎";
  edit.title = "Edit";
  edit.addEventListener("click", () => {
    loadResult(row);
    $("result").scrollIntoView({ behavior: "smooth", block: "center" });
  });
  const del = document.createElement("button");
  del.className = "secondary";
  del.textContent = "✕";
  del.title = "Delete";
  del.addEventListener("click", async () => {
    await api(`/api/history/${row.id}`, { method: "DELETE" });
    if (currentResultId === row.id) currentResultId = null;
    refreshHistory();
  });
  li.append(nko, meta, edit, del);
  return li;
}

async function updateHistoryCount() {
  try {
    const { count } = await api("/api/history/count");
    $("history-count").textContent = window.NKO_I18N.t("saved_count").replace("{n}", count);
  } catch { /* non-critical */ }
}

async function loadHistory(reset) {
  if (reset) {
    historyOffset = 0;
    $("history").replaceChildren();
  }
  try {
    const params = new URLSearchParams({ limit: HISTORY_PAGE, offset: historyOffset });
    if (historyQuery) params.set("q", historyQuery);
    const rows = await api(`/api/history?${params}`);
    const ul = $("history");
    for (const row of rows) ul.append(renderHistoryRow(row));
    historyOffset += rows.length;
    $("history-more-btn").classList.toggle("hidden", rows.length < HISTORY_PAGE);
    $("history-empty").classList.toggle("hidden", ul.childElementCount > 0);
    updateHistoryCount();
  } catch { /* history is non-critical; errors surface elsewhere */ }
}

// refreshHistory() reloads from the top (used after create/edit/delete).
function refreshHistory() { return loadHistory(true); }

let searchTimer = null;
$("history-search").addEventListener("input", (e) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    historyQuery = e.target.value.trim();
    loadHistory(true);
  }, 250);
});

$("history-more-btn").addEventListener("click", () => loadHistory(false));

$("history-clear-btn").addEventListener("click", async () => {
  const n = $("history-count").textContent;
  if (!window.confirm(`${window.NKO_I18N.t("clear_all")} — ${n}?`)) return;
  try {
    await api("/api/history", { method: "DELETE" });
    currentResultId = null;
    loadHistory(true);
  } catch (err) {
    $("app-error").textContent = err.message;
  }
});

// ---- Boot ------------------------------------------------------------------
window.NKO_I18N.initUiLanguage();
if (getToken()) showApp(); else showAuth();
