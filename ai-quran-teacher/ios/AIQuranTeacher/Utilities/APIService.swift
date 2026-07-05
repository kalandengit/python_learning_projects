import Foundation

/// Thin async client for the NestJS backend.
final class APIService {
    static let shared = APIService()

    /// Override via Info.plist key `API_BASE_URL` for TestFlight/production builds.
    var baseURL: URL = {
        if let raw = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String,
           let url = URL(string: raw) {
            return url
        }
        return URL(string: "http://localhost:3000")!
    }()

    private let session: URLSession
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()

    init(session: URLSession = .shared) {
        self.session = session
    }

    enum APIError: LocalizedError {
        case badStatus(Int, String)

        var errorDescription: String? {
            switch self {
            case let .badStatus(code, body):
                return "Server returned status \(code): \(body)"
            }
        }
    }

    // MARK: - Tajweed

    func detectTajweed(
        text: String,
        ayahId: Int,
        expectedText: String?,
        userId: String?
    ) async throws -> TajweedDetectionResult {
        struct Body: Encodable {
            let text: String
            let ayahId: Int
            let expectedText: String?
            let userId: String?
        }
        return try await post(
            "tajweed/detect",
            body: Body(text: text, ayahId: ayahId, expectedText: expectedText, userId: userId)
        )
    }

    // MARK: - Quiz

    func generateQuiz(userId: String, difficulty: QuizDifficulty, count: Int = 4) async throws -> Quiz {
        struct Body: Encodable {
            let userId: String
            let difficulty: String
            let count: Int
        }
        return try await post(
            "quiz/generate",
            body: Body(userId: userId, difficulty: difficulty.rawValue, count: count)
        )
    }

    func submitQuiz(quizId: String, answers: [Int]) async throws -> QuizResult {
        struct Body: Encodable {
            let quizId: String
            let answers: [Int]
        }
        return try await post("quiz/submit", body: Body(quizId: quizId, answers: answers))
    }

    // MARK: - Gamification

    func fetchProfile(userId: String) async throws -> GamificationProfile {
        try await get("gamification/profile/\(userId)")
    }

    func fetchLeaderboard(limit: Int = 20) async throws -> [LeaderboardEntry] {
        try await get("gamification/leaderboard?limit=\(limit)")
    }

    func recordActivity(userId: String) async throws -> StreakInfo {
        struct Body: Encodable { let userId: String }
        return try await post("gamification/activity", body: Body(userId: userId))
    }

    // MARK: - Plumbing

    private func get<Response: Decodable>(_ path: String) async throws -> Response {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = "GET"
        return try await send(request)
    }

    private func post<Body: Encodable, Response: Decodable>(
        _ path: String,
        body: Body
    ) async throws -> Response {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(body)
        return try await send(request)
    }

    private func send<Response: Decodable>(_ request: URLRequest) async throws -> Response {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw APIError.badStatus(http.statusCode, String(data: data, encoding: .utf8) ?? "")
        }
        return try decoder.decode(Response.self, from: data)
    }
}
