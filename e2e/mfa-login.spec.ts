import { expect, test } from '@playwright/test'

import { totpCode } from './support/totp'

// Opt-in journey: needs a running API (VITE_API_BASE) and a seeded account with
// MFA enabled. Provide the secret so the test can generate a live code:
//   E2E_MFA_EMAIL=... E2E_MFA_PASSWORD=... E2E_MFA_SECRET=BASE32SECRET npm run test:e2e
const email = process.env.E2E_MFA_EMAIL
const password = process.env.E2E_MFA_PASSWORD
const secret = process.env.E2E_MFA_SECRET

test.describe('second-factor sign-in', () => {
  test.skip(!email || !password || !secret, 'set E2E_MFA_EMAIL / E2E_MFA_PASSWORD / E2E_MFA_SECRET to run')

  test('rejects a wrong code and accepts the current TOTP', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('Email').fill(email!)
    await page.getByPlaceholder('Password').fill(password!)
    await page.getByRole('button', { name: /^sign in$/i }).click()

    await expect(page.getByRole('heading', { name: /two-factor verification/i })).toBeVisible()

    await page.getByPlaceholder('6-digit code').fill('000000')
    await page.getByRole('button', { name: /verify and sign in/i }).click()
    await expect(page.getByRole('heading', { name: /two-factor verification/i })).toBeVisible()
    await expect(page.getByText(/invalid/i)).toBeVisible()

    await page.getByPlaceholder('6-digit code').fill(totpCode(secret!))
    await page.getByRole('button', { name: /verify and sign in/i }).click()

    await expect(page).not.toHaveURL(/\/login/, { timeout: 15_000 })
  })

  test('the challenge never leaks a session token', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('Email').fill(email!)
    await page.getByPlaceholder('Password').fill(password!)
    await page.getByRole('button', { name: /^sign in$/i }).click()

    await expect(page.getByRole('heading', { name: /two-factor verification/i })).toBeVisible()
    expect(await page.evaluate(() => window.localStorage.getItem('access_token'))).toBeNull()
  })
})
