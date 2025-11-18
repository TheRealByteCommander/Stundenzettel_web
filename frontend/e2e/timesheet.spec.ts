import { test, expect } from "@playwright/test";

test.describe("Timesheet Management", () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto("/login");
    await page.fill('input[type="email"]', "admin@example.com");
    await page.fill('input[type="password"]', "admin123");
    await page.click('button[type="submit"]');
    
    // Handle 2FA if needed
    try {
      await page.waitForSelector("text=/2FA/i", { timeout: 2000 });
      // Skip 2FA for E2E tests - would need actual OTP
    } catch {
      // No 2FA required
    }

    await page.waitForURL("/app", { timeout: 10000 });
  });

  test("should navigate to timesheet list", async ({ page }) => {
    await page.click("text=Stundenzettel");
    await page.waitForURL("/app/timesheets");
    await expect(page.locator("h1")).toContainText("Stundenzettel");
  });

  test("should create new timesheet", async ({ page }) => {
    await page.goto("/app/timesheets");
    await page.click("text=Neuer Stundenzettel");
    await page.waitForURL("/app/timesheets/new");
    await expect(page.locator("h1")).toContainText("Neuer Stundenzettel");
  });

  test("should display timesheet list", async ({ page }) => {
    await page.goto("/app/timesheets");
    // Should show table or empty state
    await expect(
      page.locator("table, text=/Noch keine Stundenzettel/i")
    ).toBeVisible();
  });
});

