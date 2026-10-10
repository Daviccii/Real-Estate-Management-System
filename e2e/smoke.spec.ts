import { expect, test } from '@playwright/test'

// Public routes only - these run without the API so CI can smoke-test the
// bundle on its own. Authenticated journeys live in mfa-login.spec.ts.
test('home page renders the search hero', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1, name: /find property that fits your life/i })).toBeVisible()
  await expect(page.getByPlaceholder(/nairobi, mombasa, kiambu/i)).toBeVisible()
})

test('sign-in form validates locally before calling the API', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: /sign in to propnoxa/i })).toBeVisible()

  const loginCalls: string[] = []
  page.on('request', (request) => {
    if (request.url().includes('/auth/login')) loginCalls.push(request.url())
  })

  await page.getByRole('button', { name: /^sign in$/i }).click()

  await expect(page.getByText('Email is required')).toBeVisible()
  await expect(page.getByText('Password is required')).toBeVisible()
  expect(loginCalls).toEqual([])
})

test('password reveal toggle switches the input type', async ({ page }) => {
  await page.goto('/login')
  const password = page.getByPlaceholder('Password')
  await expect(password).toHaveAttribute('type', 'password')

  await page.getByRole('button', { name: /^show$/i }).click()
  await expect(password).toHaveAttribute('type', 'text')
  await page.getByRole('button', { name: /^hide$/i }).click()
  await expect(password).toHaveAttribute('type', 'password')
})

test('unauthenticated app routes fall back to sign-in', async ({ page }) => {
  await page.goto('/admin/dashboard')
  await expect(page).toHaveURL(/\/login/)
  await expect(page.getByRole('heading', { name: /sign in to propnoxa/i })).toBeVisible()
})
