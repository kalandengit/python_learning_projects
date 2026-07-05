# AI Quran Teacher — Architecture

This document describes the high-level architecture of the AI Quran Teacher
platform: an AI-assisted Quran learning application with real-time tajweed
feedback, AI-generated quizzes, live classes over WebRTC, and gamification.

The diagrams below use [Mermaid](https://mermaid.js.org/), which renders
natively on GitHub.

---

## 1. System context

```mermaid
graph TB
    subgraph Clients
        iOS["📱 iOS App<br/>(SwiftUI, MVVM)"]
        Android["🤖 Android App<br/>(Jetpack Compose, MVVM)"]
    end

    subgraph Edge
        CDN["CDN / TLS termination<br/>(reverse proxy)"]
    end

    subgraph Backend["Backend services"]
        API["NestJS REST API<br/>(auth, tajweed, quiz,<br/>gamification, quran)"]
        SIG["Signaling server<br/>(Socket.IO / WebRTC)"]
    end

    subgraph Data
        PG[("PostgreSQL")]
        REDIS[("Redis<br/>(cache + Socket.IO adapter)")]
    end

    subgraph External
        MISTRAL["Mistral AI API"]
        TURN["STUN / TURN servers"]
    end

    iOS -->|HTTPS/JSON| CDN
    Android -->|HTTPS/JSON| CDN
    iOS -->|WSS| CDN
    Android -->|WSS| CDN

    CDN --> API
    CDN --> SIG

    API --> PG
    API --> REDIS
    API -->|chat completions| MISTRAL

    SIG --> REDIS
    iOS -. peer-to-peer media .-> Android
    iOS --> TURN
    Android --> TURN
```

**Media path:** the signaling server only brokers SDP offers/answers and ICE
candidates. Once negotiated, audio/video flows **peer-to-peer** (or via a TURN
relay when NAT traversal fails) and never transits our servers, which keeps
bandwidth costs and latency low.

---

## 2. Backend module architecture (NestJS)

```mermaid
graph LR
    subgraph HTTP
        G1["ThrottlerGuard<br/>(rate limit)"]
        G2["JwtAuthGuard<br/>(authn, global)"]
        VP["ValidationPipe<br/>(DTO validation)"]
        EF["AllExceptionsFilter"]
    end

    subgraph Features
        AUTH["Users / Auth<br/>JWT + bcrypt"]
        QURAN["Quran<br/>(surahs, ayahs)"]
        TAJ["Tajweed<br/>(AI analysis)"]
        QUIZ["Quiz<br/>(AI generation + grading)"]
        GAM["Gamification<br/>(points, streaks, badges)"]
    end

    subgraph Shared
        MIS["MistralService<br/>(global)"]
        DB["DatabaseModule<br/>(TypeORM)"]
    end

    G1 --> G2 --> VP --> Features
    TAJ --> MIS
    QUIZ --> MIS
    TAJ --> QURAN
    QUIZ --> GAM
    Features --> DB
    Features -. errors .-> EF
```

Key design choices:

- **Secure by default** — a global `JwtAuthGuard` protects every route; a
  handler must opt out with `@Public()` to be reachable anonymously.
- **AI is isolated** behind `MistralService`, so features are unit-testable
  with a mock and the API key lives in exactly one place.
- **Model output is never trusted** — every AI response is validated and
  clamped before it is persisted or returned.
- **Answers stay server-side** — quiz `correctIndex` values are never sent to
  clients; grading happens on the server.

---

## 3. Tajweed analysis sequence

```mermaid
sequenceDiagram
    participant App as Mobile App
    participant API as NestJS API
    participant Q as QuranService
    participant M as Mistral AI

    App->>App: On-device speech-to-text
    App->>API: POST /api/tajweed/analyze<br/>{ surahId, ayahNumber, transcript } + JWT
    API->>API: JwtAuthGuard + ValidationPipe
    API->>Q: getAyah(surahId, ayahNumber)
    Q-->>API: reference ayah (Arabic + translit)
    API->>M: chat(system + reference + transcript, json)
    M-->>API: { score, feedback, mistakes[] }
    API->>API: sanitise + clamp + persist
    API-->>App: TajweedAnalysis
```

---

## 4. Data model (core entities)

```mermaid
erDiagram
    USER ||--o{ TAJWEED_ANALYSIS : records
    USER ||--o{ QUIZ : owns
    USER ||--|| GAMIFICATION_PROFILE : has
    QUIZ ||--o{ QUIZ_ATTEMPT : has
    SURAH ||--o{ AYAH : contains

    USER {
        uuid id PK
        string email UK
        string passwordHash
        string displayName
        string role
    }
    SURAH {
        int id PK
        string nameArabic
        int ayahCount
    }
    AYAH {
        uuid id PK
        int surahId FK
        int numberInSurah
        text textArabic
    }
    TAJWEED_ANALYSIS {
        uuid id PK
        uuid userId FK
        int score
        json mistakes
    }
    QUIZ {
        uuid id PK
        uuid userId FK
        json questions
    }
    GAMIFICATION_PROFILE {
        uuid userId PK
        int points
        int currentStreak
        json badges
    }
```

---

## 5. Deployment & scaling

```mermaid
graph TB
    LB["Load balancer"]
    subgraph API tier
        A1["API pod 1"]
        A2["API pod 2"]
        A3["API pod N"]
    end
    subgraph Signaling tier
        S1["Signaling pod 1"]
        S2["Signaling pod N"]
    end
    R[("Redis")]
    PG[("PostgreSQL<br/>primary + replicas")]

    LB --> A1 & A2 & A3
    LB --> S1 & S2
    A1 & A2 & A3 --> PG
    A1 & A2 & A3 --> R
    S1 & S2 --> R
```

Scaling notes:

- **API tier** is stateless (JWT auth, no server sessions) and scales
  horizontally behind a load balancer.
- **Signaling tier** keeps room membership in memory today. To run more than
  one instance, enable the `@socket.io/redis-adapter` so events fan out across
  pods; the `RoomRegistry` interface is deliberately small to ease that move.
- **Database**: start with a single PostgreSQL primary; add read replicas for
  leaderboard/read-heavy queries. Replace `synchronize` with migrations before
  production.
- **Caching**: cache Quran content and leaderboards in Redis (read-mostly).
- **Cost control**: AI endpoints are rate-limited per user; consider caching
  identical tajweed/quiz requests and pinning a cheaper Mistral model for
  lower tiers.

---

## 6. Security posture

| Concern | Control |
| --- | --- |
| Authentication | Stateless JWT (`@nestjs/jwt`), bcrypt password hashing (cost 12) |
| Authorization | Global `JwtAuthGuard`, ownership checks on quizzes/history |
| Transport | TLS everywhere (HTTPS + WSS), HSTS via Helmet |
| Input validation | Global `ValidationPipe` (whitelist + forbid unknown) |
| Rate limiting | `@nestjs/throttler`, tighter limits on auth and AI routes |
| Secrets | Environment variables, `.env` git-ignored, fail-fast validation |
| CORS | Explicit origin allow-list, no wildcard in production |
| AI safety | Model output validated/clamped; upstream errors never leaked |
| Headers | Helmet (CSP-ready, `X-Powered-By` disabled) |

See [`docs/SECURITY.md`](./SECURITY.md) for the full checklist.
