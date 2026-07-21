import Foundation

/// Mirrors the backend `PublicQuiz` shape (correct answers are never sent).
struct Quiz: Identifiable, Codable {
    let id: String
    let topic: String
    let difficulty: String
    let questions: [QuizQuestion]
}

struct QuizQuestion: Identifiable, Codable {
    var id: String { prompt }
    let prompt: String
    let options: [String]
}

/// Response from `POST /api/quiz/:id/submit`.
struct QuizResult: Codable {
    let attemptId: String
    let correctCount: Int
    let totalCount: Int
    let pointsAwarded: Int
    let results: [QuizAnswerResult]
}

struct QuizAnswerResult: Codable {
    let prompt: String
    let chosenIndex: Int
    let correctIndex: Int
    let correct: Bool
    let explanation: String
}
