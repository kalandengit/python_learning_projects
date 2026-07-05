# AI Quran Teacher — Android (Jetpack Compose)

A Kotlin + Jetpack Compose client for the AI Quran Teacher platform, structured
with MVVM.

> **Status: early scaffold.** These files establish the module layout,
> dependencies, and a launchable `MainActivity`. Feature screens
> (Quran Reader, Live Class, Quiz, Gamification) and the API/WebRTC layers are
> to be implemented against the backend contracts.

## Structure

```
app/src/main/java/com/example/aiquranteacher/
├── models/         data classes mirroring backend JSON
├── viewmodels/     Compose ViewModels (MVVM)
├── activities/     entry points
├── fragments/      feature screens
├── services/       API, speech, tajweed, WebRTC
├── repositories/   Room + network data sources
└── utils/          constants, extensions
```

## Networking & security

- Cleartext HTTP is **disabled** in `AndroidManifest.xml`; `network_security_config.xml`
  permits it only for `localhost` / `10.0.2.2` during development. Production
  builds must use HTTPS.
- Use Retrofit + OkHttp to call the backend (`../backend`), and Socket.IO for
  the signaling server (`../signaling-server`).

## Build

Open the `android/` folder in Android Studio (Giraffe+), let Gradle sync, and
run on an emulator or device (minSdk 24). Point the API base URL at your backend
(`http://10.0.2.2:3000/api` from the emulator).
