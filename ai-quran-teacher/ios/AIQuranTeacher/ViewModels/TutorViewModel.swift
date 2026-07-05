import Foundation

@MainActor
final class TutorViewModel: ObservableObject {
    @Published var question = ""
    @Published var response: TutorResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?

    /// Optional ayah context passed from the reader.
    var context: String?

    private let api: APIService

    init(context: String? = nil, api: APIService = .shared) {
        self.context = context
        self.api = api
    }

    func ask() async {
        let trimmed = question.trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmed.count >= 3 else { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            // Requests all four aspects; the backend generates them in parallel.
            response = try await api.askTutor(question: trimmed, context: context)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
