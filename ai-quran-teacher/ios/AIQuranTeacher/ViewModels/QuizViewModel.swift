import Foundation

@MainActor
final class QuizViewModel: ObservableObject {
    enum Phase {
        case pickingDifficulty
        case answering
        case submitting
        case finished(QuizResult)
    }

    @Published var phase: Phase = .pickingDifficulty
    @Published var quiz: Quiz?
    @Published var currentQuestionIndex = 0
    @Published var selectedAnswers: [Int?] = []
    @Published var errorMessage: String?

    private let api: APIService
    private let userId: String

    init(userId: String, api: APIService = .shared) {
        self.userId = userId
        self.api = api
    }

    var currentQuestion: QuizQuestion? {
        guard let quiz, quiz.questions.indices.contains(currentQuestionIndex) else { return nil }
        return quiz.questions[currentQuestionIndex]
    }

    var progress: Double {
        guard let quiz, !quiz.questions.isEmpty else { return 0 }
        return Double(currentQuestionIndex) / Double(quiz.questions.count)
    }

    func start(difficulty: QuizDifficulty) async {
        errorMessage = nil
        do {
            let quiz = try await api.generateQuiz(userId: userId, difficulty: difficulty)
            self.quiz = quiz
            selectedAnswers = Array(repeating: nil, count: quiz.questions.count)
            currentQuestionIndex = 0
            phase = .answering
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func select(answer index: Int) {
        guard selectedAnswers.indices.contains(currentQuestionIndex) else { return }
        selectedAnswers[currentQuestionIndex] = index
    }

    func advance() async {
        guard let quiz else { return }
        if currentQuestionIndex < quiz.questions.count - 1 {
            currentQuestionIndex += 1
        } else {
            await submit()
        }
    }

    private func submit() async {
        guard let quiz else { return }
        let answers = selectedAnswers.map { $0 ?? -1 }
        phase = .submitting
        do {
            let result = try await api.submitQuiz(quizId: quiz.id, answers: answers)
            phase = .finished(result)
        } catch {
            errorMessage = error.localizedDescription
            phase = .answering
        }
    }

    func reset() {
        quiz = nil
        selectedAnswers = []
        currentQuestionIndex = 0
        phase = .pickingDifficulty
    }
}
