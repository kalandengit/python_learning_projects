# N'Ko Voice Transcriptor for iOS

SwiftUI/WKWebView client for iOS 16+, version 1.11.0. It loads the same backend
as Android and the browser, so the shared French-based language pack is used.

1. Install XcodeGen: `brew install xcodegen`
2. Run `xcodegen generate` in this directory.
3. Open `NKoVoiceTranscriptor.xcodeproj`, choose a signing team, and run.

The first screen asks for an HTTPS backend URL. Local HTTP is accepted only for
development; use HTTPS for distribution.

The onboarding and privacy presentation take independent inspiration from
FluidVoice's language-first setup, visible runtime state, and local-first
boundaries. No FluidVoice source or assets are included; FluidVoice is GPLv3
and currently targets macOS rather than iOS.
