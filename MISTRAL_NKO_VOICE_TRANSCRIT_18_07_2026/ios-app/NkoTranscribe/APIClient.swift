import Foundation

struct TranscriptionResult: Decodable, Equatable {
    let latinText: String
    let nkoText: String
    let asrEngine: String
    let durationMs: Int?

    enum CodingKeys: String, CodingKey {
        case latinText = "latin_text"
        case nkoText = "nko_text"
        case asrEngine = "asr_engine"
        case durationMs = "duration_ms"
    }
}

struct TokenPair: Decodable {
    let accessToken: String
    let refreshToken: String

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
    }
}

enum APIError: Error {
    case http(Int)
    case invalidResponse
}

final class APIClient {

    private let session: URLSession = {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.timeoutIntervalForRequest = Config.requestTimeout
        return URLSession(configuration: configuration)
    }()

    func login(email: String, password: String) async throws {
        var request = URLRequest(url: Config.baseURL.appending(path: "/api/v1/auth/login"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(["email": email, "password": password])
        let (data, response) = try await session.data(for: request)
        try Self.checkStatus(response)
        let tokens = try JSONDecoder().decode(TokenPair.self, from: data)
        KeychainStore.set(tokens.accessToken, for: "access_token")
        KeychainStore.set(tokens.refreshToken, for: "refresh_token")
    }

    func transcribe(fileURL: URL, language: String = Config.defaultLanguage)
        async throws -> TranscriptionResult
    {
        let boundary = "nko-\(UUID().uuidString)"
        var request = URLRequest(
            url: Config.baseURL.appending(path: "/api/v1/transcriptions/upload"))
        request.httpMethod = "POST"
        request.setValue(
            "multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        if let token = KeychainStore.get("access_token") {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let audioData = try Data(contentsOf: fileURL)
        request.httpBody = Self.multipartBody(
            boundary: boundary,
            audio: audioData,
            filename: fileURL.lastPathComponent,
            fields: ["language": language]
        )
        let (data, response) = try await session.data(for: request)
        try Self.checkStatus(response)
        return try JSONDecoder().decode(TranscriptionResult.self, from: data)
    }

    static func multipartBody(
        boundary: String, audio: Data, filename: String, fields: [String: String]
    ) -> Data {
        var body = Data()
        for (name, value) in fields {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append(
                "Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n\(value)\r\n"
                    .data(using: .utf8)!)
        }
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append(
            "Content-Disposition: form-data; name=\"audio\"; filename=\"\(filename)\"\r\n"
                .data(using: .utf8)!)
        body.append("Content-Type: audio/mp4\r\n\r\n".data(using: .utf8)!)
        body.append(audio)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        return body
    }

    private static func checkStatus(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else { throw APIError.invalidResponse }
        guard (200..<300).contains(http.statusCode) else { throw APIError.http(http.statusCode) }
    }
}
