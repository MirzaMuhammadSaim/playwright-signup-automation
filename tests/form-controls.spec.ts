import { test, expect } from '@playwright/test';

test('practice checkbox', async ({ page }) => {
  await page.goto('https://www.w3schools.com/html/html_forms.asp');

  const vehicle1 = page.locator('#vehicle1');

  await vehicle1.check();

  await expect(vehicle1).toBeChecked();
});