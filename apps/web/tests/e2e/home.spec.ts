import { expect, test } from '@playwright/test';

test('landing page opens', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText(/WishWave/i).first()).toBeVisible();
});
