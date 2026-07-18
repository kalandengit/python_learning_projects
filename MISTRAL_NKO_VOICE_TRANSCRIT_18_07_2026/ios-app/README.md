# N'Ko Voice — iOS app

Native Swift / SwiftUI client for the N'Ko Voice Transcriptor backend.
Records 16 kHz mono AAC audio, uploads it to
`POST /api/v1/transcriptions/upload`, and renders Latin + right-to-left
N'Ko results. iOS ships Noto Sans NKo glyph support system-wide.

## Security posture

- Tokens in the **Keychain** (`WhenUnlockedThisDeviceOnly`), never UserDefaults.
- **App Transport Security fully enabled** — HTTPS only, no exceptions.
- Recordings live in the temp directory only and are deleted after upload.
- Ephemeral `URLSession` (no shared cookie/cache persistence).
- Microphone permission requested at use time with a clear purpose string.

## Build

```bash
# from ios-app/  (Xcode 15+, macOS 14+)
brew install xcodegen
xcodegen generate
open NkoTranscribe.xcodeproj   # build & run, or:
xcodebuild -project NkoTranscribe.xcodeproj -scheme NkoTranscribe \
  -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build
```

Set your server in `NkoTranscribe/Config.swift` (`baseURL`).

## Next steps

- Login/registration + history views (`/api/v1/auth`, `/api/v1/transcriptions`).
- Language & engine pickers from the catalog endpoints.
- Refresh-token flow via `KeychainStore` + `/api/v1/auth/refresh`.
- Certificate pinning for production.
