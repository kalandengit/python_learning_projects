"use strict";

// Lightweight client-side i18n for the interface chrome.
// en/fr/ar are full translations; nqo (N'Ko) is a best-effort starter set
// using common Manding vocabulary — flagged in the README for native review.
// Source-language ASR and the N'Ko output are unaffected by this setting.

const I18N = {
  en: {
    _name: "English", _dir: "ltr",
    app_title: "N'KO Voice Transcriptor",
    ui_language: "Interface",
    subtitle: "Speak Manding — read N'Ko",
    sign_in: "Sign in", username: "Username", password: "Password",
    log_in: "Log in", register: "Register",
    log_out: "Log out", workspace: "Transcription workspace",
    record: "Record", source_language: "Language",
    start: "● Start", standby: "❚❚ Stand by", stop: "■ Stop",
    or_upload: "…or upload an audio file:",
    nko: "N'Ko", editable_hint: "— editable, click to correct",
    latin: "Latin (Manding)",
    save_edit: "💾 Save edit", copy_nko: "⧉ Copy N'Ko", copy_latin: "⧉ Copy Latin",
    download: "Download:", try_text: "Try text directly", paste: "⎘ Paste",
    nko_keyboard: "⌨ N'Ko keyboard",
    history: "History", search_history: "Search…", clear_all: "🗑 Clear all",
    load_more: "Load more", no_history: "No history yet.",
    footer: "Manding → N'Ko (script of Solomana Kanté). Recognition quality depends on the configured ASR engine.",
    recording: "recording…", on_standby: "on stand-by", unsaved: "unsaved", saved: "✓ saved", saved_count: "{n} saved",
  },
  fr: {
    _name: "Français", _dir: "ltr",
    app_title: "Transcripteur vocal N'Ko",
    ui_language: "Interface",
    subtitle: "Parlez le mandingue — lisez le N'Ko",
    sign_in: "Connexion", username: "Nom d'utilisateur", password: "Mot de passe",
    log_in: "Se connecter", register: "S'inscrire",
    log_out: "Déconnexion", workspace: "Espace de transcription",
    record: "Enregistrer", source_language: "Langue",
    start: "● Démarrer", standby: "❚❚ Pause", stop: "■ Arrêter",
    or_upload: "…ou importez un fichier audio :",
    nko: "N'Ko", editable_hint: "— modifiable, cliquez pour corriger",
    latin: "Latin (mandingue)",
    save_edit: "💾 Enregistrer", copy_nko: "⧉ Copier le N'Ko", copy_latin: "⧉ Copier le latin",
    download: "Télécharger :", try_text: "Essayer avec du texte", paste: "⎘ Coller",
    nko_keyboard: "⌨ Clavier N'Ko",
    history: "Historique", search_history: "Rechercher…", clear_all: "🗑 Tout effacer",
    load_more: "Charger plus", no_history: "Aucun historique.",
    footer: "Mandingue → N'Ko (écriture de Solomana Kanté). La qualité de reconnaissance dépend du moteur ASR configuré.",
    recording: "enregistrement…", on_standby: "en pause", unsaved: "non enregistré", saved: "✓ enregistré", saved_count: "{n} enregistré(s)",
  },
  ar: {
    _name: "العربية", _dir: "rtl",
    app_title: "مُفرِّغ صوت النكو",
    ui_language: "الواجهة",
    subtitle: "تحدَّث الماندينغ — اقرأ النكو",
    sign_in: "تسجيل الدخول", username: "اسم المستخدم", password: "كلمة المرور",
    log_in: "دخول", register: "إنشاء حساب",
    log_out: "تسجيل الخروج", workspace: "مساحة النسخ",
    record: "تسجيل", source_language: "اللغة",
    start: "● ابدأ", standby: "❚❚ إيقاف مؤقت", stop: "■ إيقاف",
    or_upload: "…أو ارفع ملفًا صوتيًا:",
    nko: "النكو", editable_hint: "— قابل للتعديل، انقر للتصحيح",
    latin: "اللاتينية (ماندينغ)",
    save_edit: "💾 حفظ التعديل", copy_nko: "⧉ نسخ النكو", copy_latin: "⧉ نسخ اللاتينية",
    download: "تنزيل:", try_text: "جرّب النص مباشرة", paste: "⎘ لصق",
    nko_keyboard: "⌨ لوحة مفاتيح النكو",
    history: "السجل", search_history: "بحث…", clear_all: "🗑 مسح الكل",
    load_more: "تحميل المزيد", no_history: "لا يوجد سجل بعد.",
    footer: "ماندينغ → النكو (خط سليمانا كانتي). تعتمد جودة التعرّف على محرك ASR المُهيّأ.",
    recording: "جارٍ التسجيل…", on_standby: "متوقّف مؤقتًا", unsaved: "غير محفوظ", saved: "✓ تم الحفظ", saved_count: "{n} محفوظ",
  },
  nqo: {
    _name: "ߒߞߏ", _dir: "rtl",
    app_title: "ߒߞߏ ߞߊ߲ ߛߓߍߟߊ߲",
    ui_language: "ߞߊ߲",
    subtitle: "ߡߊ߲ߘߋ߲ߞߊ߲ ߝߐ߫ ߸ ߒߞߏ ߘߐߞߊߙߊ߲",
    sign_in: "ߘߏ߲߬ߠߌ߲", username: "ߕߐߜߐ", password: "ߜߎ߲ߘߏ",
    log_in: "ߘߏ߲߬", register: "ߕߐߜߐ ߛߓߍ",
    log_out: "ߓߐ߫", workspace: "ߞߊ߲ ߛߓߍߟߌ ߓߊ߯ߙߊߘߊ",
    record: "ߞߊ߲ ߡߌߣߍ", source_language: "ߞߊ߲",
    start: "● ߘߊߡߌߣߍ", standby: "❚❚ ߟߐߦߌߘߊ", stop: "■ ߟߐ",
    or_upload: "…ߥߟߊ ߞߊ߬ ߞߊ߲ ߘߐ߬ߛߙߋ ߟߊߘߏ߲߬:",
    nko: "ߒߞߏ", editable_hint: "— ߊ ߛߍߥߟߌ ߞߊ߬",
    latin: "ߟߊߕߍ߲ (ߡߊ߲ߘߋ߲ߞߊ߲)",
    save_edit: "💾 ߛߍߥߟߌ ߡߊߙߊ", copy_nko: "⧉ ߒߞߏ ߟߊߘߊߝߍ", copy_latin: "⧉ ߟߊߕߍ߲ ߟߊߘߊߝߍ",
    download: "ߊ ߟߊߖߌ߰:", try_text: "ߛߓߍߟߌ ߠߊ߫ ߞߊ߬", paste: "⎘ ߊ ߟߊߘߏ߲߬",
    nko_keyboard: "⌨ ߒߞߏ ߞߏߣߍ",
    history: "ߞߘߐߞߏ", search_history: "ߢߌߣߌ߲ߞߊ…", clear_all: "🗑 ߊ ߓߍ߯ ߖߏ߯ߛߌ",
    load_more: "ߘߏ ߟߊߘߏ߲߬", no_history: "ߞߘߐߞߏ ߕߍ߫ ߝߟߐ.",
    footer: "ߡߊ߲ߘߋ߲ߞߊ߲ → ߒߞߏ (ߛߟߏߡߊߣߊ ߞߊ߲ߕߍ ߟߊ߫ ߛߓߍߛߎ߲). ߞߊ߲ ߘߐ߬ߓߐ ߢߌߡߊ ߦߋ߫ ߛߊ߬ ASR ߡߊߛߌ߲.",
    recording: "ߞߊ߲ ߡߌߣߍ ߠߊ߫…", on_standby: "ߟߐߦߌߘߊ ߟߊ߫", unsaved: "ߡߊ ߡߊߙߊ", saved: "✓ ߡߊߙߊߣߍ߲", saved_count: "{n} ߡߊߙߊߣߍ߲",
  },
};

const UI_LANG_KEY = "nko_ui_lang";

function t(key) {
  const lang = document.documentElement.getAttribute("data-ui-lang") || "en";
  return (I18N[lang] && I18N[lang][key]) || I18N.en[key] || key;
}

function applyUiLanguage(lang) {
  if (!I18N[lang]) lang = "en";
  const dict = I18N[lang];
  document.documentElement.setAttribute("data-ui-lang", lang);
  document.documentElement.lang = lang === "nqo" ? "nqo" : lang;
  document.documentElement.dir = dict._dir;
  for (const el of document.querySelectorAll("[data-i18n]")) {
    const val = dict[el.dataset.i18n] ?? I18N.en[el.dataset.i18n];
    if (val != null) el.textContent = val;
  }
  for (const el of document.querySelectorAll("[data-i18n-placeholder]")) {
    const val = dict[el.dataset.i18nPlaceholder] ?? I18N.en[el.dataset.i18nPlaceholder];
    if (val != null) el.placeholder = val;
  }
  try { localStorage.setItem(UI_LANG_KEY, lang); } catch { /* private mode */ }
}

function initUiLanguage() {
  let lang = "en";
  try { lang = localStorage.getItem(UI_LANG_KEY) || "en"; } catch { /* ignore */ }
  const sel = document.getElementById("ui-language-select");
  if (sel) {
    // Options are generated from the dictionary: to add an interface
    // language, add one entry to I18N (with a _name) — nothing else to edit.
    sel.replaceChildren();
    for (const [code, dict] of Object.entries(I18N)) {
      const opt = document.createElement("option");
      opt.value = code;
      opt.textContent = dict._name || code;
      sel.append(opt);
    }
    if (!I18N[lang]) lang = "en";
    sel.value = lang;
    sel.addEventListener("change", () => applyUiLanguage(sel.value));
  }
  applyUiLanguage(lang);
}

window.NKO_I18N = { t, applyUiLanguage, initUiLanguage };
