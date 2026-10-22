import { test, expect } from '@playwright/test';

test('click and verify link', async ({ page }) => {
  // Open website
  await page.goto('https://example.com');

  // Verify heading
  await expect(page.locator('h1')).toHaveText('Example Domain');

  // Find the link
  const moreInfoLink = page.getByRole('link', {
    name: 'More information...'
  });

  // Verify link is visible
  await expect(moreInfoLink).toBeVisible();

  // Click the link
  await moreInfoLink.click();

  // Verify we moved to IANA website
  await expect(page).toHaveURL(/iana.org/);
});