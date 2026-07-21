# AI Quran Teacher — iOS (SwiftUI)

A SwiftUI + MVVM client for the AI Quran Teacher platform.

> **Status: early scaffold.** These files establish the architecture and the
> Quran Reader vertical. They are not yet a buildable Xcode target — an
> `.xcodeproj` and asset catalog must be generated, and the `LiveClass`,
> `Quiz`, and `Gamification` features are stubs to be filled in.

## Architecture

- **MVVM** — SwiftUI `View`s bind to `ObservableObject` view models.
- **Models** mirror the backend JSON contracts (`Surah`, `Ayah`, `Quiz`, `Badge`, …).
- **APIService** — `URLSession` client targeting the backend routes documented
  in [`../backend/README.md`](../backend/README.md). Set `baseURL` and
  `authToken` from configuration / the auth flow.
- **SpeechRecognizer** — on-device Arabic STT (`SFSpeechRecognizer`).
- **TajweedEngine** — fast local hints; authoritative analysis comes from
  `POST /api/tajweed/analyze`.
- **WebRTC** — live classes connect to the signaling server (see
  [`../signaling-server`](../signaling-server)).

## Getting started

1. Create an Xcode project (iOS 16+) named `AIQuranTeacher` and add these sources.
2. Add package dependencies (Speech, AVFoundation are system frameworks;
   add a WebRTC package for live classes).
3. Point `APIService.baseURL` at your backend.
4. Ensure the Info.plist usage strings (mic, speech, camera) are present.

## Roadmap

- [ ] Xcode project + asset catalog
- [ ] Auth screens wired to `/api/auth`
- [ ] Live class (WebRTC) view models and views
- [ ] Quiz and Gamification screens
- [ ] Real on-device speech recognition and local tajweed heuristics
