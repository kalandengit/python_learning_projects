import { describe, expect, it } from 'vitest'
import { generatedDocumentToMarkdown } from '@/lib/markdown'
import type { GeneratedDocument } from '@/lib/validators/document'

const sampleDocument: GeneratedDocument = {
  title: 'Upload a screenshot',
  summary: 'This guide explains how to upload a screenshot and generate documentation.',
  audience: 'end_user',
  document_type: 'help_article',
  confidence_score: 0.91,
  detected_ui: {
    app_or_page_name: 'Upload page',
    primary_goal: 'Upload an image',
    visible_elements: ['Project selector'],
    forms: ['Upload form'],
    buttons: ['Generate documentation'],
    navigation_items: ['Dashboard']
  },
  steps: [
    {
      order: 1,
      title: 'Choose a screenshot',
      instruction: 'Select a screenshot from your computer before starting the upload.',
      expected_result: 'The file is ready to upload.',
      ui_elements: ['File input'],
      tip: 'Use PNG files for best readability.'
    }
  ],
  warnings: ['Avoid uploading secrets or production credentials.'],
  tips: ['Crop screenshots to the relevant area.'],
  faq: [
    {
      question: 'Can I edit the generated article?',
      answer: 'Yes, generated documentation can be edited before export.'
    }
  ],
  metadata: {
    language: 'en',
    generated_at: '2026-07-08T00:00:00.000Z',
    model: 'gpt-4o-mini',
    provider: 'openai'
  }
}

describe('generatedDocumentToMarkdown', () => {
  it('renders a complete editable markdown document', () => {
    const markdown = generatedDocumentToMarkdown(sampleDocument)

    expect(markdown).toContain('# Upload a screenshot')
    expect(markdown).toContain('## Detected interface')
    expect(markdown).toContain('### 1. Choose a screenshot')
    expect(markdown).toContain('> Tip: Use PNG files for best readability.')
    expect(markdown).toContain('## FAQ')
  })
})
