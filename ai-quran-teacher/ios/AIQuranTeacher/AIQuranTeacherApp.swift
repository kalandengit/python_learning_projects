import SwiftUI

@main
struct AIQuranTeacherApp: App {
    // Replace with real authentication (see AuthModule in the backend); a stable
    // anonymous ID keeps progress, quizzes, exams, and streaks working before
    // sign-in ships.
    @AppStorage("userId") private var userId = UUID().uuidString

    init() {
        // Tint the whole app with the brand emerald.
        UITabBar.appearance().tintColor = UIColor(Theme.emerald)
    }

    var body: some Scene {
        WindowGroup {
            TabView {
                SurahListView()
                    .tabItem { Label("Read", systemImage: "book") }

                TutorView(viewModel: TutorViewModel())
                    .tabItem { Label("Tutor", systemImage: "sparkles") }

                ExamView(viewModel: ExamViewModel(userId: userId))
                    .tabItem { Label("Exams", systemImage: "rosette") }

                QuizView(viewModel: QuizViewModel(userId: userId))
                    .tabItem { Label("Quiz", systemImage: "questionmark.circle") }

                GamificationView(viewModel: GamificationViewModel(userId: userId))
                    .tabItem { Label("Progress", systemImage: "chart.bar") }
            }
            .tint(Theme.emerald)
            .environment(\.managedObjectContext, CoreDataManager.shared.viewContext)
        }
    }
}
