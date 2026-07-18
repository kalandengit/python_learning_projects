"use strict";

const I18N = {
  en: {
    title: "N'Ko Voice Transcriptor", login: "Log in", logout: "Log out",
    account: "Account", register: "Register", transcribe: "Transcribe",
    language: "Language", engine: "Engine", record: "● Record", stop: "■ Stop",
    save_history: "Save to history", latin: "Latin", nko: "N'Ko",
    keyboard: "N'Ko keyboard", dictionary: "Dictionary (Français ↔ ߒߞߏ)",
    search: "Search…", search_btn: "Search", history: "History",
    email: "Email", password: "Password (min 10 characters)",
    privacy_note: "Audio is processed in memory and discarded — only text is stored, and only if you ask.",
  },
  fr: {
    title: "Transcripteur vocal N'Ko", login: "Connexion", logout: "Déconnexion",
    account: "Compte", register: "Créer un compte", transcribe: "Transcrire",
    language: "Langue", engine: "Moteur", record: "● Enregistrer", stop: "■ Arrêter",
    save_history: "Garder dans l'historique", latin: "Latin", nko: "N'Ko",
    keyboard: "Clavier N'Ko", dictionary: "Dictionnaire (Français ↔ ߒߞߏ)",
    search: "Rechercher…", search_btn: "Rechercher", history: "Historique",
    email: "Adresse e-mail", password: "Mot de passe (10 caractères min.)",
    privacy_note: "L'audio est traité en mémoire puis supprimé — seul le texte est conservé, et uniquement si vous le demandez.",
  },
  ar: {
    title: "ناسخ الصوت بحروف النكو", login: "تسجيل الدخول", logout: "تسجيل الخروج",
    account: "الحساب", register: "إنشاء حساب", transcribe: "نسخ",
    language: "اللغة", engine: "المحرك", record: "● تسجيل", stop: "■ إيقاف",
    save_history: "حفظ في السجل", latin: "لاتيني", nko: "نكو",
    keyboard: "لوحة مفاتيح النكو", dictionary: "قاموس (فرنسي ↔ ߒߞߏ)",
    search: "بحث…", search_btn: "بحث", history: "السجل",
    email: "البريد الإلكتروني", password: "كلمة المرور (10 أحرف على الأقل)",
    privacy_note: "تتم معالجة الصوت في الذاكرة ثم يُحذف — يُحفظ النص فقط وعند طلبك.",
  },
  nqo: {
    title: "ߒߞߏ ߞߊ߲ߛߓߍߟߊ߲", login: "ߘߏ߲߬ߠߌ߲", logout: "ߓߐߟߌ",
    account: "ߖߊ߬ߕߋ߬ߘߊ", register: "ߖߊ߬ߕߋ߬ߘߊ ߟߊߘߊ߲", transcribe: "ߛߓߍߦߊߟߌ",
    language: "ߞߊ߲", engine: "ߡߊ߬ߛߌ߲", record: "● ߞߎߡߊߕߊ", stop: "■ ߟߊߟߐ߬",
    save_history: "ߘߐ߬ߝߐ ߟߊߞߛߌ", latin: "ߟߊߕߍ߲", nko: "ߒߞߏ",
    keyboard: "ߒߞߏ ߛߓߍߟߊ߲", dictionary: "ߘߊ߰ߘߐ߬ߞߊ߲ (ߝߊ߬ߙߊ߲߬ߛߌ ↔ ߒߞߏ)",
    search: "ߢߌߣߌ߲…", search_btn: "ߢߌߣߌ߲", history: "ߘߐ߬ߝߐ",
    email: "ߓߊ߬ߕߊ", password: "ߕߐ߰ߡߊ߬ߛߙߋ (10 ߛߓߍߘߋ߲)",
    privacy_note: "ߞߎߡߊߞߊ߲ ߓߊ߯ߙߊ ߞߍߕߐ߫ ߦߋ߲߬ ߠߋ߬ ߞߊ߬ ߓߊ߲߫ ߞߵߊ߬ ߖߏ߰ߛߌ߬ — ߛߓߍߟߌ ߘߐߙߐ߲߫ ߠߋ߬ ߟߊߞߛߌߕߐ߫.",
  },
};

const RTL_LANGS = new Set(["ar", "nqo"]);

function applyI18n(lang) {
  const table = I18N[lang] || I18N.en;
  document.documentElement.lang = lang;
  document.documentElement.dir = RTL_LANGS.has(lang) ? "rtl" : "ltr";
  for (const el of document.querySelectorAll("[data-i18n]")) {
    const key = el.getAttribute("data-i18n");
    if (table[key]) el.textContent = table[key];
  }
  for (const el of document.querySelectorAll("[data-i18n-placeholder]")) {
    const key = el.getAttribute("data-i18n-placeholder");
    if (table[key]) el.setAttribute("placeholder", table[key]);
  }
  sessionStorage.setItem("ui-lang", lang);
}
