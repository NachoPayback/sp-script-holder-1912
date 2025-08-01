import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Remote Control Hub/);
});

test('auth form is visible', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#authForm')).toBeVisible();
});

test('can toggle between login and signup', async ({ page }) => {
  await page.goto('/');
  
  const toggleButton = page.locator('button:has-text("New user? Sign up here")');
  await expect(toggleButton).toBeVisible();
  
  await toggleButton.click();
  await expect(page.locator('button:has-text("Sign Up")')).toBeVisible();
  
  const backToLoginButton = page.locator('button:has-text("Already have an account? Sign in")');
  await backToLoginButton.click();
  await expect(page.locator('button:has-text("Sign In")')).toBeVisible();
});