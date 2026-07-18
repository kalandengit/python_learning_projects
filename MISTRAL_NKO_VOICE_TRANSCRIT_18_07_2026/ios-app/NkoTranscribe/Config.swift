import Foundation

enum Config {
    /// Point at your deployment. App Transport Security enforces HTTPS;
    /// for the simulator against a local backend use an ATS debug exception
    /// or a local HTTPS proxy — never disable ATS in release builds.
    static let baseURL = URL(string: "https://nko.example.com")!
    static let defaultLanguage = "bam"
    static let requestTimeout: TimeInterval = 60
}
