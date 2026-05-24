import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  fetchAutomationRunGraph,
  fetchAutomationRunGraphs,
} from './automationApi';

describe('automationApi run graph helpers', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('requests run graphs list with limit and optional status', async () => {
    globalThis.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ graphs: [{ id: 'r1' }] }),
    });

    const result = await fetchAutomationRunGraphs(15, 'success');

    expect(result).toEqual([{ id: 'r1' }]);
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    expect(globalThis.fetch.mock.calls[0][0]).toContain('/automation/graphs?limit=15&status=success');
  });

  it('returns null when run id is empty', async () => {
    const result = await fetchAutomationRunGraph('');
    expect(result).toBeNull();
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it('requests single run graph by run id', async () => {
    globalThis.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ graph: { id: 'run-123' } }),
    });

    const result = await fetchAutomationRunGraph('run-123');

    expect(result).toEqual({ id: 'run-123' });
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    expect(globalThis.fetch.mock.calls[0][0]).toContain('/automation/runs/run-123/graph');
  });
});
