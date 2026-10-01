const { chromium } = require("playwright");
const fs = require("fs");

const [url, mode, imagePath, screenshotPath] = process.argv.slice(2);

if (!url || !mode || !imagePath) {
  throw new Error("Usage: node phase5_round2_browser_acceptance.js URL round1|round2 IMAGE [SCREENSHOT]");
}

async function clickNavigation(page, label) {
  if (mode === "round1") {
    await page.getByRole("tab", { name: label, exact: true }).click();
  } else {
    await page.getByText(label, { exact: true }).first().click();
  }
  await page.getByRole("heading", { name: label, exact: true }).waitFor();
}

async function submitQuestion(page, question) {
  const input = page.getByLabel("你想了解什么？");
  await input.fill(question);
  await page.getByRole("button", { name: /获取可信回答/ }).click();
  await page.waitForTimeout(500);
}

async function main() {
  const bundledChromium = chromium.executablePath();
  const edge = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
  const executablePath = process.env.BROWSER_EXECUTABLE
    || (fs.existsSync(bundledChromium) ? bundledChromium : edge);
  const browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", error => pageErrors.push(String(error)));
  page.on("console", message => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.goto(url, { waitUntil: "domcontentloaded" });
  await page.getByText("南京云锦智能识别与数字化传承", { exact: true }).waitFor();

  await clickNavigation(page, "AI识锦");
  await page.locator('input[type="file"]').setInputFiles(imagePath);
  const analyzeButton = page.getByRole("button", { name: /开始 AI 分析/ });
  await analyzeButton.waitFor();
  await analyzeButton.click();
  await page.getByText("当前视觉线索不足以匹配到高可信度的文化知识。", { exact: true }).waitFor();
  const scenarioA = true;

  if (mode === "round1") {
    await page.getByRole("button", { name: /前往 AI文化助手/ }).click();
    await page.getByLabel("你想了解什么？").waitFor();
    await submitQuestion(page, "妆花是什么？");
    await page.getByText(/挖花盘织/).last().waitFor();
  } else {
    await clickNavigation(page, "AI文化助手");
    await submitQuestion(page, "妆花是什么？");
    await page.getByText(/挖花盘织/).last().waitFor();
    await page.getByText("查看知识来源与证据", { exact: true }).click();
    await page.getByText(/中国非物质文化遗产网/).first().waitFor();
  }
  const scenarioB = true;

  const repeatedQuestions = [
    "南京云锦有哪些主要品种？",
    "云锦为什么需要手工织造？",
    "八宝纹有什么文化寓意？",
  ];
  if (mode === "round2") {
    await clickNavigation(page, "AI识锦");
    await page.locator('input[type="file"]').setInputFiles(imagePath);
    await page.getByRole("button", { name: /开始 AI 分析/ }).click();
    await page.getByText("当前视觉线索不足以匹配到高可信度的文化知识。", { exact: true }).waitFor();
    await page.getByRole("button", { name: "妆花是什么？", exact: true }).first().click();
    await page.getByLabel("你想了解什么？").waitFor();
  }
  for (const [index, question] of repeatedQuestions.entries()) {
    if (mode === "round1") {
      await clickNavigation(page, "AI识锦");
      await page.getByRole("button", { name: /前往 AI文化助手/ }).click();
      await page.getByLabel("你想了解什么？").waitFor();
    } else if (index > 0) {
      await clickNavigation(page, "AI识锦");
      await clickNavigation(page, "AI文化助手");
    }
    await submitQuestion(page, question);
  }
  const scenarioC = true;

  if (screenshotPath) {
    await page.screenshot({ path: screenshotPath, fullPage: true });
  }

  const relevantErrors = [...pageErrors, ...consoleErrors].filter(text =>
    /removeChild|NotFoundError|React DOM/i.test(text)
  );
  console.log(JSON.stringify({ mode, scenarioA, scenarioB, scenarioC, pageErrors, consoleErrors, relevantErrors }, null, 2));
  await browser.close();
  if (relevantErrors.length) process.exitCode = 2;
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
