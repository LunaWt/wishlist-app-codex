import { describe, expect, it } from 'vitest';

import { formatMoney, safePercent } from '@/lib/utils';

describe('utils', () => {
  it('formats currency in ru locale', () => {
    const formatted = formatMoney(1500, 'RUB');
    expect(formatted).toContain('₽');
  });

  it('clamps percent', () => {
    expect(safePercent(120)).toBe(100);
    expect(safePercent(-20)).toBe(0);
  });
});
