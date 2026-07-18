package com.nko.voice

import com.nko.voice.api.ApiClient
import org.junit.Assert.assertEquals
import org.junit.Test

class ApiClientTest {

    @Test
    fun parsesTranscriptionPayload() {
        val payload = """
            {"id": null, "latin_text": "i ni ce", "nko_text": "ߌ ߣߌ ߗߋ",
             "language": "bam", "asr_engine": "mock", "duration_ms": 12}
        """.trimIndent()
        val result = ApiClient.parseTranscription(payload)
        assertEquals("i ni ce", result.latinText)
        assertEquals("ߌ ߣߌ ߗߋ", result.nkoText)
        assertEquals("mock", result.engine)
        assertEquals(12L, result.durationMs)
    }
}
