import SwiftUI

@main
struct AIQuranTeacherApp: App {
    // Replace with real authentication; a stable anonymous ID keeps
    // progress, quizzes, and streaks working before sign-in ships.
    @AppStorage("userId") private var userId = UUID().uuidString

    var body: some Scene {
        WindowGroup {
            TabView {
                SurahListView()
                    .tabItem { Label("Read", systemImage: "book") }

                QuizView(viewModel: QuizViewModel(userId: userId))
                    .tabItem { Label("Quiz", systemImage: "questionmark.circle") }

                GamificationView(viewModel: GamificationViewModel(userId: userId))
                    .tabItem { Label("Progress", systemImage: "chart.bar") }
            }
            .environment(\.managedObjectContext, CoreDataManager.shared.viewContext)
        }
    }
}
