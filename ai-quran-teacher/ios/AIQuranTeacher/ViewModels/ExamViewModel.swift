import Foundation

@MainActor
final class ExamViewModel: ObservableObject {
    enum Phase {
        case pickingLevel
        case inProgress
        case submitting
        case finished(ExamResult)
    }

    @Published var phase: Phase = .pickingLevel
    @Published var exam: Exam?
    @Published var currentIndex = 0
    @Published var answers: [Int?] = []
    @Published var secondsRemaining = 0
    @Published var errorMessage: String?

    private let api: APIService
    private let userId: String
    private var timer: Timer?

    init(userId: String, api: APIService = .shared) {
        self.userId = userId
        self.api = api
    }

    var currentQuestion: QuizQuestion? {
        guard let exam, exam.questions.indices.contains(currentIndex) else { return nil }
        return exam.questions[currentIndex]
    }

    var timeString: String {
        String(format: "%02d:%02d", secondsRemaining / 60, secondsRemaining % 60)
    }

    func start(level: ExamLevel) async {
        errorMessage = nil
        do {
            let exam = try await api.startExam(userId: userId, level: level)
            self.exam = exam
            answers = Array(repeating: nil, count: exam.questions.count)
            currentIndex = 0
            secondsRemaining = Int(exam.expiresAt.timeIntervalSinceNow)
            phase = .inProgress
            startTimer()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func select(_ index: Int) {
        guard answers.indices.contains(currentIndex) else { return }
        answers[currentIndex] = index
    }

    func advance() async {
        guard let exam else { return }
        if currentIndex < exam.questions.count - 1 {
            currentIndex += 1
        } else {
            await submit()
        }
    }

    func submit() async {
        guard let exam else { return }
        timer?.invalidate()
        phase = .submitting
        do {
            let result = try await api.submitExam(
                examId: exam.id,
                answers: answers.map { $0 ?? -1 }
            )
            phase = .finished(result)
        } catch {
            errorMessage = error.localizedDescription
            phase = .inProgress
        }
    }

    func reset() {
        timer?.invalidate()
        exam = nil
        answers = []
        currentIndex = 0
        phase = .pickingLevel
    }

    private func startTimer() {
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
            Task { @MainActor in
                guard let self else { return }
                if self.secondsRemaining > 0 {
                    self.secondsRemaining -= 1
                } else {
                    // Time's up — auto-submit whatever is answered.
                    await self.submit()
                }
            }
        }
    }
}
