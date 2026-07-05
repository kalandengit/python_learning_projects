import { Test } from '@nestjs/testing';
import { CompletionRequest, LlmService } from '../llm/llm.service';
import { TutorService } from './tutor.service';

describe('TutorService', () => {
  let service: TutorService;
  let parallelMock: jest.Mock;

  beforeEach(async () => {
    // Simulate the LLM by echoing each aspect's prompt; records concurrency.
    parallelMock = jest.fn(async (requests: CompletionRequest[]) =>
      requests.map((r) => ({
        result: {
          text: `answer for: ${r.prompt.slice(0, 20)}`,
          model: 'claude-opus-4-8',
          inputTokens: 10,
          outputTokens: 20,
        },
      })),
    );

    const moduleRef = await Test.createTestingModule({
      providers: [
        TutorService,
        { provide: LlmService, useValue: { enabled: true, parallel: parallelMock } },
      ],
    }).compile();
    service = moduleRef.get(TutorService);
  });

  it('fans out one request per requested aspect in a single parallel batch', async () => {
    const response = await service.ask('What is Tajweed?', undefined, [
      'answer',
      'tajweed',
    ]);
    // All aspects dispatched together (the parallel primitive), not sequentially.
    expect(parallelMock).toHaveBeenCalledTimes(1);
    expect(parallelMock.mock.calls[0][0]).toHaveLength(2);
    expect(response.aspects.map((a) => a.aspect)).toEqual(['answer', 'tajweed']);
    expect(response.aspects.every((a) => a.text)).toBe(true);
  });

  it('aggregates token usage across aspects', async () => {
    const response = await service.ask('Explain Surah Al-Fatihah', undefined, [
      'answer',
      'tafsir',
      'followUp',
    ]);
    expect(response.usage.inputTokens).toBe(30);
    expect(response.usage.outputTokens).toBe(60);
  });

  it('uses higher effort and thinking for the main answer only', async () => {
    await service.ask('question', undefined, ['answer', 'tajweed']);
    const dispatched: CompletionRequest[] = parallelMock.mock.calls[0][0];
    const answerReq = dispatched[0];
    const tajweedReq = dispatched[1];
    expect(answerReq.effort).toBe('high');
    expect(answerReq.think).toBe(true);
    expect(tajweedReq.effort).toBe('low');
    expect(tajweedReq.think).toBe(false);
  });

  it('surfaces per-aspect failures without failing the whole response', async () => {
    parallelMock.mockResolvedValueOnce([
      { result: { text: 'ok', model: 'm', inputTokens: 1, outputTokens: 1 } },
      { error: 'rate limited' },
    ]);
    const response = await service.ask('q', undefined, ['answer', 'tafsir']);
    expect(response.aspects[0].text).toBe('ok');
    expect(response.aspects[1].error).toBe('rate limited');
  });

  it('includes the ayah context in every aspect prompt when provided', async () => {
    await service.ask('Why this word?', 'بِسْمِ اللَّهِ', ['answer']);
    const dispatched: CompletionRequest[] = parallelMock.mock.calls[0][0];
    expect(dispatched[0].prompt).toContain('بِسْمِ اللَّهِ');
  });
});
