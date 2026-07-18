# N'Ko Voice — Android app

Native Kotlin / Jetpack Compose client for the N'Ko Voice Transcriptor
backend. Records 16 kHz mono AAC audio, uploads it to
`POST /api/v1/transcriptions/upload`, and renders the result in Latin and
right-to-left N'Ko script.

## Security posture

- Tokens stored in `EncryptedSharedPreferences` (Android Keystore).
- Cleartext traffic disabled; the release build must point at HTTPS
  (`API_BASE_URL` in `app/build.gradle.kts`).
- Recordings live only in the app cache and are deleted right after upload.
- Microphone permission requested at runtime.

## Build

```bash
# from android-app/  (Android Studio 2023+ / JDK 17 / SDK 34)
gradle assembleDebug          # or ./gradlew if you generate the wrapper
gradle testDebugUnitTest
```

The debug build targets `http://10.0.2.2:8000` (host machine from the
emulator) so it works against `uvicorn app.main:app` out of the box.

## Next steps

- Login/registration screen wired to `ApiClient.login` + history view.
- Language & engine pickers (`GET /api/v1/languages`, `/api/v1/asr/engines`).
- Bundle Noto Sans NKo for guaranteed N'Ko glyph rendering on older devices.
- Certificate pinning for production deployments.
