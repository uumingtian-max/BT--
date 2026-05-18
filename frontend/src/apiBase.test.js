import { describe, it, expect } from 'vitest';

describe('api base', () => {
  it('defaults to local backend', () => {
    const api = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
    expect(api).toMatch(/^https?:\/\//);
  });
});
