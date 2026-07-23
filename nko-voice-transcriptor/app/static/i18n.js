"use strict";

// Language engine. Translation catalogs live separately in languages.js.
// French is the reference catalog: every other language is validated against it.
const UI_LANG_KEY = "nko_ui_lang";
const REFERENCE_LANGUAGE = "fr";

function catalogs() { return window.NKO_LANGUAGE_PACK || {}; }

function validateCatalogs() {
  const all = catalogs();
  const reference = all[REFERENCE_LANGUAGE];
  if (!reference) throw new Error("Missing French reference language catalog");
  const required = Object.keys(reference).filter((key) => !key.startsWith("_"));
  for (const [code, catalog] of Object.entries(all)) {
    const missing = required.filter((key) => catalog[key] == null);
    if (missing.length) console.warn(`Language ${code} is missing: ${missing.join(", ")}`);
  }
}

function currentLanguage() {
  return document.documentElement.getAttribute("data-ui-lang") || REFERENCE_LANGUAGE;
}

function t(key, variables = {}) {
  const all = catalogs();
  const value = all[currentLanguage()]?.[key] ?? all[REFERENCE_LANGUAGE]?.[key] ?? key;
  return Object.entries(variables).reduce(
    (text, [name, replacement]) => text.replaceAll(`{${name}}`, String(replacement)),
    value,
  );
}

function applyUiLanguage(lang) {
  const all = catalogs();
  if (!all[lang]) lang = REFERENCE_LANGUAGE;
  const catalog = all[lang];
  document.documentElement.setAttribute("data-ui-lang", lang);
  document.documentElement.lang = lang;
  document.documentElement.dir = catalog._dir;
  document.title = catalog.app_title;
  for (const el of document.querySelectorAll("[data-i18n]")) {
    el.textContent = t(el.dataset.i18n);
  }
  for (const el of document.querySelectorAll("[data-i18n-placeholder]")) {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  }
  try { localStorage.setItem(UI_LANG_KEY, lang); } catch { /* private mode */ }
  window.dispatchEvent(new CustomEvent("nko:languagechange", { detail: { lang } }));
}

function initUiLanguage() {
  validateCatalogs();
  const all = catalogs();
  let lang = navigator.language?.split("-")[0] || REFERENCE_LANGUAGE;
  try { lang = localStorage.getItem(UI_LANG_KEY) || lang; } catch { /* ignore */ }
  if (!all[lang]) lang = REFERENCE_LANGUAGE;
  const select = document.getElementById("ui-language-select");
  if (select) {
    select.replaceChildren(...Object.entries(all).map(([code, catalog]) => {
      const option = document.createElement("option");
      option.value = code;
      option.textContent = catalog._name || code;
      return option;
    }));
    select.value = lang;
    select.addEventListener("change", () => applyUiLanguage(select.value));
  }
  applyUiLanguage(lang);
}

window.NKO_I18N = { t, applyUiLanguage, initUiLanguage, REFERENCE_LANGUAGE };
