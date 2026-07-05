import Foundation

enum QuizDifficulty: String, Codable, CaseIterable, Identifiable {
    case easy, medium, hard
    var id: String { rawValue }
}

/// A quiz served by `POST /quiz/generate`. Correct answers stay server-side.
struct Quiz: Identifiable, Codable {
    let id: String
    let difficulty: QuizDifficulty
    let questions: [QuizQuestion]
}

struct QuizQuestion: Identifiable, Codable, Hashable {
    let id: String
    let question: String
    let options: [String]
}

/// Result of `POST /quiz/submit`.
struct QuizResult: Codable {
    struct ReviewItem: Codable, Identifiable {
        let questionId: String
        let correct: Bool
        let correctIndex: Int
        let explanation: String
        var id: String { questionId }
    }

    let quizId: String
    let score: Int
    let total: Int
    let xpEarned: Int
    let newBadges: [String]
    let review: [ReviewItem]
}
