# N'Ko Voice Transcriptor — Android test client

A minimal, dependency-free **WebView** app that loads the N'Ko Voice
Transcriptor web UI from a server you specify. It exists so you can install a
**test APK** on an Android device and use the app (including microphone
recording) natively.

> The APK has **no backend of its own** — it needs a running N'Ko Voice
> Transcriptor server (`uvicorn app.main:app`). On **first launch** it asks for
> the server URL, and if the server is **unreachable** it shows a "Server
> unreachable" dialog with **Retry** / **Change URL**. Use the ⋮ menu →
> **Set server URL** to change it at any time.

- `versionName` **1.8.1**, `versionCode` 10801 (see `app/build.gradle`).
- `minSdk` 26, `targetSdk`/`compileSdk` 34, no AndroidX.
- Microphone permission is requested and forwarded to the WebView so in-page
  recording works. Cleartext HTTP is allowed (test build) so you can point at a
  LAN dev server; use HTTPS for anything real.

## Getting the APK

The APK is built in CI, not in this sandbox (no Android SDK here). Push to the
branch or run the **nko-android-apk** workflow manually; it:

1. builds `assembleDebug`,
2. uploads `nko-voice-transcriptor-1.8.1-debug.apk` as a workflow **artifact**, and
3. publishes it to a **prerelease** (`apk-v1.8.1`) for a direct download link.

Download it, enable "Install unknown apps" for your browser/file manager, and
install. Then enter your server URL:

- Android emulator on the same machine as the server: `http://10.0.2.2:8000`
- Physical device on the same Wi‑Fi: `http://<your-computer-LAN-IP>:8000`

## Build locally (with an Android SDK)

```bash
cd nko-voice-transcriptor/android
gradle wrapper --gradle-version 8.7
./gradlew assembleDebug
# APK at app/build/outputs/apk/debug/app-debug.apk
```
