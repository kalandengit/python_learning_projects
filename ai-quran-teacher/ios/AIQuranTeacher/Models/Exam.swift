import Foundation

enum ExamLevel: String, Codable, CaseIterable, Identifiable {
    case foundation, intermediate, advanced
    var id: String { rawValue }

    var title: String {
        switch self {
        case .foundation: "Foundation"
        case .intermediate: "Intermediate"
        case .advanced: "Advanced"
        }
    }
}

/// A timed exam served by `POST /exams/start`.
struct Exam: Identifiable, Codable {
    let id: String
    let level: ExamLevel
    let durationMinutes: Int
    let startedAt: Date
    let expiresAt: Date
    let passPercent: Int
    let questions: [QuizQuestion]
}

/// Result of `POST /exams/submit`.
struct ExamResult: Codable {
    let examId: String
    let level: ExamLevel
    let score: Int
    let total: Int
    let percent: Int
    let passed: Bool
    let expired: Bool
    let xpEarned: Int
    let certificate: Certificate?
    let review: [QuizResult.ReviewItem]
}

/// A certification earned by passing an exam.
struct Certificate: Identifiable, Codable {
    let id: String
    let userId: String
    let examId: String
    let level: ExamLevel
    let verificationCode: String
    let issuedAt: Date
}

/// Response of `GET /exams/verify/:code`.
struct CertificateVerification: Codable {
    let valid: Bool
    let level: ExamLevel?
    let issuedAt: Date?
    let certificateId: String?
}
