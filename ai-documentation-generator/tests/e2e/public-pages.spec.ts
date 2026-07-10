import { expect, test } from '@playwright/test'

test('marketing homepage loads', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/AI Documentation Generator/i)
})

test('pricing page loads', async ({ page }) => {
  await page.goto('/pricing')
  await expect(page.getByRole('heading', { name: /pricing/i })).toBeVisible()
})
