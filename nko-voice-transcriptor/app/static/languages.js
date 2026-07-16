"use strict";

// N'Ko Voice language pack v1.8.0.
// French (`fr`) is the canonical source. Keep all catalogs key-for-key aligned
// with it. Bambara (`bm`) was translated from the French meanings, as requested.
window.NKO_LANGUAGE_PACK = {
  fr: {
    _name: "Français", _dir: "ltr", app_title: "Transcripteur vocal N'Ko",
    ui_language: "Interface", subtitle: "Parlez le mandingue — lisez le N'Ko",
    sign_in: "Connexion", username: "Nom d'utilisateur", password: "Mot de passe",
    log_in: "Se connecter", register: "S'inscrire", log_out: "Déconnexion",
    workspace: "Espace de transcription", record: "Enregistrer", source_language: "Langue",
    start: "● Démarrer", standby: "❚❚ Pause", resume: "▶ Reprendre", stop: "■ Arrêter",
    or_upload: "…ou importez un fichier audio :", nko: "N'Ko",
    editable_hint: "— modifiable, cliquez pour corriger", latin: "Latin (mandingue)",
    save_edit: "💾 Enregistrer", copy_nko: "⧉ Copier le N'Ko", copy_latin: "⧉ Copier le latin",
    copied: "✓ Copié", copy_blocked: "✗ Copie bloquée", download: "Télécharger :",
    try_text: "Essayer avec du texte", paste: "⎘ Coller", nko_keyboard: "⌨ Clavier N'Ko",
    history: "Historique", search_history: "Rechercher…", clear_all: "🗑 Tout effacer",
    load_more: "Charger plus", no_history: "Aucun historique.", recording: "enregistrement…",
    on_standby: "en pause", unsaved: "non enregistré", saved: "✓ enregistré",
    saved_count: "{n} enregistré(s)", dictionary_title: "Dictionnaire",
    dict_placeholder: "Chercher un mot…", search: "🔍 Rechercher", dict_none: "Aucun résultat.",
    dict_credit: "Lexique : NKo Wuruki / Institut N'Ko.", microphone_denied: "Accès au microphone refusé — vous pouvez importer un fichier.",
    session_expired: "Session expirée — reconnectez-vous.", request_failed: "Échec de la requête",
    clipboard_denied: "Lecture du presse-papiers bloquée — utilisez Ctrl+V / ⌘V.",
    footer: "Mandingue → N'Ko (écriture de Solomana Kanté). La qualité dépend du moteur de reconnaissance configuré."
  },
  bm: {
    _name: "Bamanankan", _dir: "ltr", app_title: "N'Ko kumakan sɛbɛnnikɛlan",
    ui_language: "Kankurunkan", subtitle: "Mandingekan fɔ — N'Ko kalan",
    sign_in: "Don", username: "Baarakɛla tɔgɔ", password: "Gundo kumakan",
    log_in: "I ka don", register: "I tɔgɔ sɛbɛn", log_out: "I ka bɔ",
    workspace: "Kumakan sɛbɛn yɔrɔ", record: "Kumakan ta", source_language: "Kan",
    start: "● A daminɛ", standby: "❚❚ A jɔ", resume: "▶ A daminɛ kokura", stop: "■ A lajɔ",
    or_upload: "…walima, kumakan filen bila yan :", nko: "N'Ko",
    editable_hint: "— se ka ladilan, a digi ka tiɲɛ", latin: "Latɛnkanna (mandingekan)",
    save_edit: "💾 A mara", copy_nko: "⧉ N'Ko sɛbɛn kopi", copy_latin: "⧉ Latɛnkanna kopi",
    copied: "✓ A kopira", copy_blocked: "✗ Kopi ma sɔn", download: "A lajigin :",
    try_text: "Sɛbɛnni lajɛ", paste: "⎘ A nɔrɔ", nko_keyboard: "⌨ N'Ko klaviyeti",
    history: "Kɔrɔlenw", search_history: "Ɲini…", clear_all: "🗑 Bɛɛ jɔsi",
    load_more: "Dɔw wɛrɛ jira", no_history: "Kɔrɔlen si tɛ yen.", recording: "kumakan tali…",
    on_standby: "a jɔra", unsaved: "a ma mara", saved: "✓ a marara",
    saved_count: "{n} marara", dictionary_title: "Daɲɛgafe",
    dict_placeholder: "Daɲɛ ɲini…", search: "🔍 Ɲini", dict_none: "Foyi ma sɔrɔ.",
    dict_credit: "Daɲɛgafe : NKo Wuruki / N'Ko Institute.", microphone_denied: "Mikoro ma sɔn — i bɛ se ka kumakan filen bila yan.",
    session_expired: "Don waati banna — i ka don kokura.", request_failed: "Ɲinini ma se ka kɛ",
    clipboard_denied: "Kopi yɔrɔ kalan ma sɔn — Ctrl+V / ⌘V kɛ.",
    footer: "Mandingekan → N'Ko (Solomana Kanté ka sɛbɛnni). Tiɲɛni ka ɲi ka bɛn kumakan dɔnni min bɛ baarala."
  },
  en: {
    _name: "English", _dir: "ltr", app_title: "N'Ko Voice Transcriptor", ui_language: "Interface",
    subtitle: "Speak Manding — read N'Ko", sign_in: "Sign in", username: "Username", password: "Password",
    log_in: "Log in", register: "Register", log_out: "Log out", workspace: "Transcription workspace",
    record: "Record", source_language: "Language", start: "● Start", standby: "❚❚ Pause", resume: "▶ Resume", stop: "■ Stop",
    or_upload: "…or upload an audio file:", nko: "N'Ko", editable_hint: "— editable, click to correct", latin: "Latin (Manding)",
    save_edit: "💾 Save edit", copy_nko: "⧉ Copy N'Ko", copy_latin: "⧉ Copy Latin", copied: "✓ Copied", copy_blocked: "✗ Copy blocked",
    download: "Download:", try_text: "Try text directly", paste: "⎘ Paste", nko_keyboard: "⌨ N'Ko keyboard", history: "History",
    search_history: "Search…", clear_all: "🗑 Clear all", load_more: "Load more", no_history: "No history yet.", recording: "recording…",
    on_standby: "paused", unsaved: "unsaved", saved: "✓ saved", saved_count: "{n} saved", dictionary_title: "Dictionary",
    dict_placeholder: "Search for a word…", search: "🔍 Search", dict_none: "No match.", dict_credit: "Lexicon: NKo Wuruki / N'Ko Institute.",
    microphone_denied: "Microphone access denied — you can upload a file instead.", session_expired: "Session expired — please log in again.",
    request_failed: "Request failed", clipboard_denied: "Clipboard read blocked — paste with Ctrl+V / ⌘V.",
    footer: "Manding → N'Ko (script of Solomana Kanté). Quality depends on the configured speech-recognition engine."
  },
  ru: {
    _name: "Русский", _dir: "ltr", app_title: "Голосовой транскриптор N'Ko", ui_language: "Интерфейс", subtitle: "Говорите на манден — читайте на N'Ko",
    sign_in: "Вход", username: "Имя пользователя", password: "Пароль", log_in: "Войти", register: "Регистрация", log_out: "Выйти",
    workspace: "Рабочая область транскрипции", record: "Запись", source_language: "Язык", start: "● Начать", standby: "❚❚ Пауза", resume: "▶ Продолжить", stop: "■ Остановить",
    or_upload: "…или загрузите аудиофайл:", nko: "N'Ko", editable_hint: "— можно редактировать", latin: "Латиница (манден)", save_edit: "💾 Сохранить",
    copy_nko: "⧉ Копировать N'Ko", copy_latin: "⧉ Копировать латиницу", copied: "✓ Скопировано", copy_blocked: "✗ Копирование запрещено", download: "Скачать:",
    try_text: "Попробовать текст", paste: "⎘ Вставить", nko_keyboard: "⌨ Клавиатура N'Ko", history: "История", search_history: "Поиск…", clear_all: "🗑 Очистить всё",
    load_more: "Загрузить ещё", no_history: "История пуста.", recording: "идёт запись…", on_standby: "пауза", unsaved: "не сохранено", saved: "✓ сохранено", saved_count: "Сохранено: {n}",
    dictionary_title: "Словарь", dict_placeholder: "Найти слово…", search: "🔍 Найти", dict_none: "Совпадений нет.", dict_credit: "Словарь: NKo Wuruki / Институт N'Ko.",
    microphone_denied: "Доступ к микрофону запрещён — загрузите аудиофайл.", session_expired: "Сеанс истёк — войдите снова.", request_failed: "Ошибка запроса",
    clipboard_denied: "Чтение буфера обмена запрещено — используйте Ctrl+V / ⌘V.", footer: "Манден → N'Ko (письмо Соломаны Канте). Качество зависит от настроенного распознавания речи."
  },
  zh: {
    _name: "中文", _dir: "ltr", app_title: "N'Ko 语音转写器", ui_language: "界面语言", subtitle: "说曼丁语 — 阅读 N'Ko",
    sign_in: "登录", username: "用户名", password: "密码", log_in: "登录", register: "注册", log_out: "退出登录", workspace: "转写工作区",
    record: "录音", source_language: "语言", start: "● 开始", standby: "❚❚ 暂停", resume: "▶ 继续", stop: "■ 停止", or_upload: "…或上传音频文件：",
    nko: "N'Ko", editable_hint: "— 可编辑，点击修正", latin: "拉丁字母（曼丁语）", save_edit: "💾 保存修改", copy_nko: "⧉ 复制 N'Ko", copy_latin: "⧉ 复制拉丁文字",
    copied: "✓ 已复制", copy_blocked: "✗ 无法复制", download: "下载：", try_text: "直接输入文字", paste: "⎘ 粘贴", nko_keyboard: "⌨ N'Ko 键盘",
    history: "历史记录", search_history: "搜索…", clear_all: "🗑 全部清除", load_more: "加载更多", no_history: "暂无历史记录。", recording: "正在录音…", on_standby: "已暂停",
    unsaved: "未保存", saved: "✓ 已保存", saved_count: "已保存 {n} 条", dictionary_title: "词典", dict_placeholder: "搜索词语…", search: "🔍 搜索", dict_none: "无匹配结果。",
    dict_credit: "词典：NKo Wuruki / N'Ko 研究所。", microphone_denied: "麦克风访问被拒绝 — 您可以上传音频文件。", session_expired: "会话已过期 — 请重新登录。",
    request_failed: "请求失败", clipboard_denied: "无法读取剪贴板 — 请使用 Ctrl+V / ⌘V。", footer: "曼丁语 → N'Ko（索洛马纳·坎特创制的文字）。质量取决于所配置的语音识别引擎。"
  },
  ar: {
    _name: "العربية", _dir: "rtl", app_title: "مُفرّغ صوت N'Ko", ui_language: "لغة الواجهة", subtitle: "تحدّث بالماندينغ — واقرأ بالنكو",
    sign_in: "تسجيل الدخول", username: "اسم المستخدم", password: "كلمة المرور", log_in: "دخول", register: "إنشاء حساب", log_out: "تسجيل الخروج",
    workspace: "مساحة التفريغ", record: "تسجيل", source_language: "اللغة", start: "● ابدأ", standby: "❚❚ إيقاف مؤقت", resume: "▶ متابعة", stop: "■ إيقاف",
    or_upload: "…أو ارفع ملفًا صوتيًا:", nko: "النكو", editable_hint: "— قابل للتعديل، انقر للتصحيح", latin: "اللاتينية (ماندينغ)", save_edit: "💾 حفظ التعديل",
    copy_nko: "⧉ نسخ النكو", copy_latin: "⧉ نسخ اللاتينية", copied: "✓ تم النسخ", copy_blocked: "✗ تعذر النسخ", download: "تنزيل:", try_text: "جرّب النص مباشرة",
    paste: "⎘ لصق", nko_keyboard: "⌨ لوحة مفاتيح النكو", history: "السجل", search_history: "بحث…", clear_all: "🗑 مسح الكل", load_more: "تحميل المزيد", no_history: "لا يوجد سجل بعد.",
    recording: "جارٍ التسجيل…", on_standby: "متوقف مؤقتًا", unsaved: "غير محفوظ", saved: "✓ تم الحفظ", saved_count: "{n} محفوظ", dictionary_title: "قاموس",
    dict_placeholder: "ابحث عن كلمة…", search: "🔍 بحث", dict_none: "لا نتائج.", dict_credit: "المعجم: NKo Wuruki / معهد النكو.", microphone_denied: "رُفض الوصول إلى الميكروفون — يمكنك رفع ملف صوتي.",
    session_expired: "انتهت الجلسة — سجّل الدخول مجددًا.", request_failed: "فشل الطلب", clipboard_denied: "تعذرت قراءة الحافظة — استخدم Ctrl+V / ⌘V.",
    footer: "الماندينغ ← النكو (خط سليمانا كانتي). تعتمد الجودة على محرك التعرّف على الكلام المُعدّ."
  },
  nqo: {
    _name: "ߒߞߏ", _dir: "rtl", app_title: "ߒߞߏ ߞߊ߲ ߛߓߍߟߌ߲", ui_language: "ߞߊ߲", subtitle: "ߡߊ߲ߘߋ߲ ߞߊ߲ ߝߐ߫ — ߒߞߏ ߞߊ߬ߙߊ߲߬",
    sign_in: "ߘߏ߲߬ߠߌ߲", username: "ߟߊ߬ߓߊ߯ߙߊ߬ߟߊ ߕߐ߮", password: "ߜߎ߲ߘߎߞߎߡߊ", log_in: "ߘߏ߲߬", register: "ߕߐ߮ ߛߓߍ߫", log_out: "ߓߐ߫",
    workspace: "ߞߊ߲ ߛߓߍߟߌ߲ ߞߍߦߌߙߊ", record: "ߞߊ߲ ߡߌ߬ߘߊ߬", source_language: "ߞߊ߲", start: "● ߘߊߡߌ߬ߣߊ߬", standby: "❚❚ ߟߊߞߏߟߏ߲", resume: "▶ ߘߊߡߌ߬ߣߊ߬ ߞߏ߫", stop: "■ ߟߊ߬ߟߐ߬",
    or_upload: "…ߥߟߊ߫ ߞߊ߲ ߞߐߕߐ߮ ߟߊߦߟߍ߬:", nko: "ߒߞߏ", editable_hint: "— ߊ߬ ߘߌ߫ ߛߋ߫ ߟߊߛߊ߬ߦߌ߬ ߟߊ߫", latin: "ߟߊߕߍ߲ (ߡߊ߲ߘߋ߲)", save_edit: "💾 ߊ߬ ߟߊߡߊߙߊ߫",
    copy_nko: "⧉ ߒߞߏ ߓߊߖߎߡߊ߫", copy_latin: "⧉ ߟߊߕߍ߲ ߓߊߖߎߡߊ߫", copied: "✓ ߊ߬ ߓߊߖߎߡߊ߫ ߘߊ߫", copy_blocked: "✗ ߓߊߖߎߡߊߟߌ ߡߊ߫ ߛߐ߲߬", download: "ߟߊߖߌ߲߰:",
    try_text: "ߛߓߍߟߌ߲ ߟߊߞߘߐߓߐ߫", paste: "⎘ ߊ߬ ߣߐ߯", nko_keyboard: "⌨ ߒߞߏ ߞߏߘߏ߲", history: "ߞߐߕߐ߮", search_history: "ߢߌߣߌ߲…", clear_all: "🗑 ߓߍ߯ ߖߏ߬ߛߌ߬", load_more: "ߜߘߍ߫ ߟߎ߬ ߦߌ߬ߘߊ߬", no_history: "ߞߐߕߐ߮ ߕߍ߫.",
    recording: "ߞߊ߲ ߡߌ߬ߘߊ߬ߟߌ…", on_standby: "ߊ߬ ߟߐ߬ ߘߊ߫", unsaved: "ߊ߬ ߡߊ߫ ߡߊߙߊ߬", saved: "✓ ߊ߬ ߡߊߙߊ߫ ߘߊ߫", saved_count: "{n} ߡߊߙߊ߫ ߘߊ߫", dictionary_title: "ߞߎߡߘߊߞߎ߲", dict_placeholder: "ߞߎߡߊ߫ ߢߌߣߌ߲…", search: "🔍 ߢߌߣߌ߲", dict_none: "ߝߏߦߌ߬ ߡߊ߫ ߛߐ߬ߘߐ߲߬.",
    dict_credit: "ߞߎߡߘߊߞߎ߲: NKo Wuruki / N'Ko Institute.", microphone_denied: "ߞߊ߲ߡߌߘߊߟߊ߲ ߡߊ߫ ߛߐ߲߬ — ߞߊ߲ ߞߐߕߐ߮ ߟߊߦߟߍ߬.", session_expired: "ߘߏ߲߬ߠߌ߲ ߕߎ߬ߡߊ ߓߊ߲߫ ߘߊ߫ — ߌ ߘߏ߲߬ ߞߏ߫.", request_failed: "ߢߌߣߌ߲ߠߌ߲ ߡߊ߫ ߛߎߘߎ߲߫",
    clipboard_denied: "ߓߊߖߎߡߊ ߦߙߐ ߞߊ߬ߙߊ߲ ߡߊ߫ ߛߐ߲߬ — Ctrl+V / ⌘V ߞߍ߫.", footer: "ߡߊ߲ߘߋ߲ → ߒߞߏ (ߛߏ߬ߟߏ߬ߡߊ߬ߣߊ߫ ߞߊ߲ߕߍ߫ ߟߊ߫ ߛߓߍߟߌ߲). ߞߊ߲ ߘߐ߲ߠߌ߲ ߞߍߢߊ ߟߋ߬ ߦߋ߫ ߊ߬ ߟߊ߫."
  }
};
