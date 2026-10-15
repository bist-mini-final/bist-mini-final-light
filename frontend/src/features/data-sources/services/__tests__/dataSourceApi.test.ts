import { afterEach, describe, expect, it, vi } from 'vitest';
import { dataSourceApi } from '../dataSourceApi';

describe('dataSourceApi', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('surfaces the message from the current structured API error envelope', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({
        detail: {
          code: 'WORKFLOW_QUEUE_UNAVAILABLE',
          message: 'Local 실행 큐를 사용할 수 없습니다',
          retryable: true,
          context: {},
        },
      }),
      { status: 503, headers: { 'Content-Type': 'application/json' } },
    )));

    await expect(dataSourceApi.getDbStatus()).rejects.toMatchObject({
      message: 'Local 실행 큐를 사용할 수 없습니다',
      status: 503,
    });
  });

  it('uses the configured server embedding model unless explicitly overridden', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(
      JSON.stringify({}),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    ));
    vi.stubGlobal('fetch', fetchMock);

    await dataSourceApi.uploadFile(new File(['sheet'], 'sample.xlsx'));

    expect(fetchMock).toHaveBeenCalledOnce();
    const request = fetchMock.mock.calls[0]?.[0];
    expect(request).toBeInstanceOf(Request);
    expect(new URL((request as Request).url).searchParams.has('model')).toBe(false);
  });

  it('preserves an explicitly selected local model on upload', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { headers: { 'Content-Type': 'application/json' } }));
    vi.stubGlobal('fetch', fetchMock);
    await dataSourceApi.uploadFile(new File(['sheet'], 'sample.xlsx'), true, 'llamacpp:bge-m3');
    expect(new URL((fetchMock.mock.calls[0][0] as Request).url).searchParams.get('model')).toBe('llamacpp:bge-m3');
  });
});
