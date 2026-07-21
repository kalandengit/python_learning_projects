# ASR engines and Manding suitability

This reviews the speech-to-text landscape (see the full survey archived at
[`nko-research/stt-repertoire.md`](nko-research/stt-repertoire.md)) against
this project's actual requirement: **transcribing Manding speech** (Bambara,
Dyula, Maninka…) for conversion to N'Ko.

## The honest headline

**Meta MMS remains the only mainstream engine with real Manding support.**
Most of the celebrated STT stack does not cover these languages at all:

| Engine / family | Manding support | Notes |
|---|---|---|
| **Meta MMS** (`facebook/mms-1b-all`) | ✅ `bam`, `dyu`, `emk`, `mku`, `msc`, `mwk` adapters | What this app ships (`NKO_ASR_ENGINE=mms`). Research-grade accuracy. |
| OpenAI Whisper / faster-whisper / whisper.cpp / WhisperKit | ❌ | Whisper's 99-language set has **no Bambara/Manding** — it will force-fit another language. |
| Vosk | ❌ | No Manding model published. |
| sherpa-onnx / k2 | ❌ | No Manding model in the model zoo. |
| NVIDIA NeMo / Parakeet | ❌ | Multilingual sets exclude Manding. |
| SenseVoice | ❌ | Mandarin/Cantonese/English/Japanese/Korean. |
| Coqui STT / DeepSpeech | ❌ (and unmaintained) | Would require training from scratch. |
| Cloud APIs (Google, Azure, AWS, Deepgram, AssemblyAI, …) | ❌/⚠️ | None list Bambara as a supported transcription language today. |

Conclusion: engine *choice* is not where Manding quality will come from —
**data** is (see "Improving quality" below).

## Plugging in a custom engine

The engine layer is pluggable. `NKO_ASR_ENGINE` accepts:

- `mock` — deterministic, dependency-free (tests/demos),
- `mms` — Meta MMS with per-language adapter hot-swap (production),
- a dotted path **`package.module:ClassName`** — any class that subclasses
  `app.asr.base.ASREngine` and accepts `(settings)`.

Example: an experimental faster-whisper engine (knowing it cannot target
Manding — useful only for comparative experiments):

```python
# myengines/fw.py
from app.asr.base import ASREngine, ASRResult

class FasterWhisperEngine(ASREngine):
    name = "faster-whisper"
    def __init__(self, settings):
        from faster_whisper import WhisperModel
        self._model = WhisperModel("small", compute_type="int8")
    def transcribe(self, audio, audio_format, language="bam"):
        import io
        segments, _ = self._model.transcribe(io.BytesIO(audio))
        return ASRResult(text_latin=" ".join(s.text for s in segments),
                         engine=self.name, language=language)
```

```bash
NKO_ASR_ENGINE=myengines.fw:FasterWhisperEngine uvicorn app.main:app
```

The app fail-fasts at startup if the path doesn't resolve to an `ASREngine`.

## Improving quality (the real levers)

1. **Evaluation corpus** — [Mozilla Common Voice](https://commonvoice.mozilla.org/)
   hosts open, crowd-sourced voice data including Manding-language
   contributions; pair recorded clips with the N'Ko lexicon to measure WER
   honestly before/after any engine change.
2. **Fine-tuning MMS** — the MMS adapters are fine-tunable; a modest curated
   Bambara corpus beats swapping engines.
3. **Post-editing UX** — the app already ships the editable output, N'Ko
   keyboard with tone marks, and dictionary insert; those remain the honest
   compensation for research-grade ASR.
