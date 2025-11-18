import { test, expect } from "@playwright/test";

test.describe("Login Flow", () => {
  test("should login successfully with valid credentials", async ({ page }) => {
    await page.goto("/login");

    // Fill in login form
    await page.fill('input[type="email"]', "admin@example.com");
    await page.fill('input[type="password"]', "admin123");

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for navigation to dashboard
    await page.waitForURL("/app", { timeout: 10000 });

    // Check if we're on the dashboard
    await expect(page.locator("h1")).toContainText("Willkommen");
  });

  test("should show error with invalid credentials", async ({ page }) => {
    await page.goto("/login");

    await page.fill('input[type="email"]', "invalid@example.com");
    await page.fill('input[type="password"]', "wrongpassword");

    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator("text=/Fehler|Ungültig/i")).toBeVisible({
      timeout: 5000,
    });
  });

  test("should require 2FA after initial login", async ({ page }) => {
    await page.goto("/login");

    await page.fill('input[type="email"]', "admin@example.com");
    await page.fill('input[type="password"]', "admin123");

    await page.click('button[type="submit"]');

    // Should show 2FA dialog
    await expect(page.locator("text=/2FA|Authentifizierung/i")).toBeVisible({
      timeout: 5000,
    });
  });
});

