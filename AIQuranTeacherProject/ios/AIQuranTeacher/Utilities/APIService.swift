import Foundation

/// Networking client for the AI Quran Teacher backend.
///
/// Uses `URLSession` (no third-party dependency) and targets the documented
/// backend routes (see `backend/README.md`). The base URL and bearer token
/// should be injected from configuration / the auth flow rather than hard-coded.
final class APIService {
    static let shared = APIService()

    /// Point this at your deployed backend, e.g. `https://api.example.com/api`.
    var baseURL = URL(string: "http://localhost:3000/api")!
    /// Set after login/registration.
    var authToken: String?

    private let session = URLSession.shared
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

    private init() {}

    enum APIError: Error { case invalidResponse, http(Int), noData }

    /// The backend's tajweed analysis response (`POST /api/tajweed/analyze`).
    private struct TajweedAnalysisResponse: Codable {
        let score: Int
        let feedback: String
        let mistakes: [BackendMistake]

        struct BackendMistake: Codable {
            let word: String
            let position: Int?
            let rule: String
            let severity: String
            let explanation: String
            let correction: String
        }
    }

    func analyzeTajweed(
        surahId: Int,
        ayahNumber: Int,
        transcript: String,
        completion: @escaping (Result<[TajweedMistake], Error>) -> Void
    ) {
        let body: [String: Any] = [
            "surahId": surahId,
            "ayahNumber": ayahNumber,
            "transcript": transcript
        ]
        post("/tajweed/analyze", body: body) { [decoder] (result: Result<Data, Error>) in
            switch result {
            case .success(let data):
                do {
                    let response = try decoder.decode(TajweedAnalysisResponse.self, from: data)
                    let mistakes = response.mistakes.enumerated().map { index, m in
                        TajweedMistake(
                            id: UUID(),
                            ayahId: ayahNumber,
                            rule: TajweedRule(rawValue: m.rule) ?? .makharij,
                            position: m.position ?? index,
                            severity: Severity(rawValue: m.severity) ?? .minor,
                            suggestion: m.correction
                        )
                    }
                    completion(.success(mistakes))
                } catch {
                    completion(.failure(error))
                }
            case .failure(let error):
                completion(.failure(error))
            }
        }
    }

    // MARK: - Helpers

    private func post(_ path: String, body: [String: Any], completion: @escaping (Result<Data, Error>) -> Void) {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        session.dataTask(with: request) { data, response, error in
            if let error = error { return completion(.failure(error)) }
            guard let http = response as? HTTPURLResponse else {
                return completion(.failure(APIError.invalidResponse))
            }
            guard (200..<300).contains(http.statusCode) else {
                return completion(.failure(APIError.http(http.statusCode)))
            }
            guard let data = data else { return completion(.failure(APIError.noData)) }
            completion(.success(data))
        }.resume()
    }
}
