# AI Quran Teacher — iOS App

SwiftUI app for iPhone/iPad: Quran reader with real-time Tajweed feedback,
live classes (WebRTC), quizzes, and gamification. All Swift sources in
`AIQuranTeacher/` are complete; what remains is the Xcode project shell,
which must be created on a Mac.

## Creating the Xcode project

1. **New project**: Xcode → File → New → Project → iOS App.
   - Product Name: `AIQuranTeacher`, Interface: SwiftUI, Language: Swift.
   - Create it in this `ios/` directory, then delete the generated
     `ContentView.swift` and `AIQuranTeacherApp.swift` and add the existing
     `AIQuranTeacher/` folder (Models, Views, ViewModels, Utilities,
     Resources) to the target.

2. **Core Data model**: File → New → File → Data Model, named
   `AIQuranTeacher` (placed in `Utilities/CoreData/`). Entities:

   | Entity | Attributes | Relationships |
   |---|---|---|
   | `SurahEntity` | id: Int32, name, englishName, englishMeaning, revelationType, numberOfAyahs: Int32 | `ayahs` → AyahEntity (to-many, cascade) |
   | `AyahEntity` | id: Int32, surahId: Int32, numberInSurah: Int32, text, translation | `surah` → SurahEntity (inverse) |
   | `BookmarkEntity` | ayahId: Int32, createdAt: Date | — |
   | `ProgressEntity` | surahId: Int32, lastAyahId: Int32, updatedAt: Date | — |
   | `RecitationSessionEntity` | id: UUID, ayahId: Int32, accuracy: Double, recordedAt: Date | `mistakes` → TajweedMistakeEntity (to-many, cascade) |
   | `TajweedMistakeEntity` | type, severity, wordIndex: Int32, expectedWord, actualWord, suggestion | `session` → RecitationSessionEntity (inverse) |

3. **Swift Package dependencies** (File → Add Package Dependencies):
   - `https://github.com/stasel/WebRTC` — WebRTC framework (`WebRTCManager.swift`)
   - `https://github.com/socketio/socket.io-client-swift` — Socket.IO (`SignalingClient.swift`)

4. **Info.plist**: use `AIQuranTeacher/Resources/Info.plist` (microphone,
   speech recognition, and camera usage descriptions; background audio;
   `API_BASE_URL` and `SIGNALING_URL` endpoints).

5. **Quran data**: add a `quran.json` file to the bundle — an array of
   `Surah` objects (see `Models/Surah.swift`). The text of all 114 surahs
   with translations can be exported from the Tanzil project
   (https://tanzil.net/download/) and converted to this shape.

6. Run on a simulator or device. Speech recognition requires a real device
   for best results; Arabic locale `ar-SA` must be available.

## Architecture

- **Models/** — Codable structs mirroring the backend API shapes.
- **ViewModels/** — `@MainActor ObservableObject`s; all backend calls go
  through `Utilities/APIService.swift`.
- **Utilities/TajweedEngine.swift** — on-device fallback of the backend rule
  engine so feedback still works offline (keep in sync with
  `backend/src/tajweed/tajweed.rules.ts`).
- **Utilities/WebRTC/** — `WebRTCManager` (peer connection, camera capture)
  and `SignalingClient` (Socket.IO) used by `LiveClassViewModel`.
- **Offline mode** — Core Data via `CoreDataManager` stores bookmarks and
  recitation sessions; surah text ships in the bundle.
