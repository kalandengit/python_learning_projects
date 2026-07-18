"""Static catalogs served by /api/v1/languages and /api/v1/asr/engines."""

LANGUAGES = [
    {"code": "bam", "name": "Bambara", "native_name": "Bamanankan", "region": "Mali"},
    {"code": "dyu", "name": "Dyula", "native_name": "Julakan", "region": "West Africa"},
    {"code": "mnk", "name": "Mandinka", "native_name": "Mandinka", "region": "Senegambia"},
    {"code": "emk", "name": "Maninka", "native_name": "Maninkakan", "region": "Guinea, Mali"},
    {"code": "jul", "name": "Julula", "native_name": "Julula", "region": "Senegal, Gambia"},
    {"code": "fr", "name": "French", "native_name": "Français", "region": "—"},
    {"code": "en", "name": "English", "native_name": "English", "region": "—"},
]

ENGINES = [
    {
        "id": "mock",
        "name": "Mock (development)",
        "model": "deterministic",
        "languages": ["*"],
        "requires": None,
    },
    {
        "id": "mms",
        "name": "Meta MMS",
        "model": "facebook/mms-1b-all",
        "languages": ["bam", "dyu", "mnk", "emk", "jul", "+1100 more"],
        "requires": "torch/torchaudio/transformers + model download",
    },
    {
        "id": "whisper",
        "name": "Whisper Large v3",
        "model": "openai/whisper-large-v3",
        "languages": ["fr", "en", "+97 more"],
        "requires": "torch/torchaudio/transformers + model download",
    },
    {
        "id": "voxtral",
        "name": "Mistral Voxtral Transcribe",
        "model": "voxtral-mini-latest",
        "languages": ["en", "fr", "es", "de", "it", "pt", "nl", "hi", "zh", "ar", "ru", "ja", "ko"],
        "requires": "NKO_MISTRAL_API_KEY",
    },
]
