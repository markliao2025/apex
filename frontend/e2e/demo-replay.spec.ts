import { expect, test } from "@playwright/test";
import type { Download } from "@playwright/test";

async function downloadText(download: Download): Promise<string> {
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf8");
}

test("keyboard user completes the synthetic replay and evidence journey", async ({
  page,
}) => {
  const consoleErrors: string[] = [];
  const requestFailures: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("requestfailed", (request) => {
    requestFailures.push(
      `${request.method()} ${request.url()}: ${request.failure()?.errorText}`,
    );
  });

  await page.goto("/login");
  await expect(page.getByText("Demo data is synthetic and not for operational decisions.")).toBeVisible();

  const emailBox = await page.getByLabel("Email", { exact: true }).boundingBox();
  const passwordBox = await page
    .getByLabel("Password", { exact: true })
    .boundingBox();
  expect(emailBox?.width).toBe(passwordBox?.width);
  await expect(page.getByRole("button", { name: "Show password" })).toBeVisible();

  for (let index = 0; index < 6; index += 1) {
    await page.keyboard.press("Tab");
  }
  const demoButton = page.getByRole("button", {
    name: "Try the synthetic demo — no account needed",
  });
  await expect(demoButton).toBeFocused();
  await page.keyboard.press("Enter");

  await expect(page).toHaveURL(/\/demo\/replay$/);
  await expect(
    page.getByText(
      "Research and decision-support software. Not flight-certified. No maneuver is executed by Apex. Synthetic data only.",
    ),
  ).toBeVisible();
  await expect(page.getByLabel("Constellation")).toHaveValue(/.+/);
  await expect(
    page.getByLabel("Hypothetically unavailable satellite"),
  ).toHaveValue(/.+/);

  await page.getByRole("button", { name: "Run deterministic replay" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Provided risk, degraded evidence quality",
    }),
  ).toBeVisible();
  await expect(page.getByText("Pc provided · not computed")).toBeVisible();
  await expect(page.getByText(/fixture sha256: [a-f0-9]{64}/)).toBeVisible();
  await expect(page.getByText(/Covariance is unavailable/)).toBeVisible();

  await page.getByRole("button", { name: "Compare schedule" }).click();
  await expect(
    page.getByRole("heading", { name: "Schedule comparison complete" }),
  ).toBeVisible();
  await expect(page.getByText("1 planned task")).toBeVisible();
  await expect(page.getByText("0 planned task")).toBeVisible();
  await expect(page.getByText(/impact sha256: [a-f0-9]{64}/)).toBeVisible();

  for (const format of ["JSON", "MD"]) {
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: format, exact: true }).click();
    const content = (await downloadText(await downloadPromise)).toLowerCase();
    expect(content).toContain("not flight-certified");
    expect(content).toContain("no maneuver");
    expect(content).toContain("provided");
    expect(content).toContain("not compute");
    expect(content.includes("sha256") || content.includes("sha-256")).toBe(true);
  }

  for (const viewport of [
    { width: 375, height: 812 },
    { width: 768, height: 1024 },
    { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    const dimensions = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
    }));
    expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
  }

  expect(requestFailures).toEqual([]);
  expect(consoleErrors).toEqual([]);
});
