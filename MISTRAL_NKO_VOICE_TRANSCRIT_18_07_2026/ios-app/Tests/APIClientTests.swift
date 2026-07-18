import XCTest
@testable import NkoTranscribe

final class APIClientTests: XCTestCase {

    func testDecodesTranscriptionPayload() throws {
        let payload = """
        {"id": null, "latin_text": "i ni ce", "nko_text": "ߌ ߣߌ ߗߋ",
         "language": "bam", "asr_engine": "mock", "duration_ms": 12}
        """.data(using: .utf8)!
        let result = try JSONDecoder().decode(TranscriptionResult.self, from: payload)
        XCTAssertEqual(result.latinText, "i ni ce")
        XCTAssertEqual(result.nkoText, "ߌ ߣߌ ߗߋ")
        XCTAssertEqual(result.asrEngine, "mock")
        XCTAssertEqual(result.durationMs, 12)
    }

    func testMultipartBodyContainsFieldsAndAudio() {
        let body = APIClient.multipartBody(
            boundary: "b", audio: Data([0x52, 0x49, 0x46, 0x46]),
            filename: "a.m4a", fields: ["language": "bam"]
        )
        let text = String(decoding: body, as: UTF8.self)
        XCTAssertTrue(text.contains("name=\"language\""))
        XCTAssertTrue(text.contains("filename=\"a.m4a\""))
        XCTAssertTrue(text.contains("--b--"))
    }
}
