const { test, expect } = require("@playwright/test");

test("homepage loads successfully", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveTitle("DevOps Portfolio App");

  await expect(
    page.getByRole("heading", { name: "DevOps Portfolio App" })
  ).toBeVisible();
});
