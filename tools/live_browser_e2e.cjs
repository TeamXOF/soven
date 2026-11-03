const { chromium } = require('C:/Users/Ace/AppData/Roaming/npm/node_modules/google-flow-browser-mcp/node_modules/playwright-core');
const fs = require('fs');
const path = require('path');

const OUT_DIR = path.resolve('D:/[Project]/SOVEN/.qa/live_browser_screenshots');
if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

(async () => {
  console.log('[BROWSER] Launching Chromium...');
  const browser = await chromium.launch({
    headless: true,
    args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    permissions: ['microphone']
  });

  const page = await context.newPage();
  const base = 'http://localhost:3000';

  console.log('[1/6] Navigating to Landing Page:', base);
  await page.goto(base + '/');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: path.join(OUT_DIR, '01_landing_page.png'), fullPage: true });
  console.log('      Captured 01_landing_page.png');

  console.log('[2/6] Navigating to /try (Microphone Test)...');
  await page.goto(base + '/try');
  await page.getByRole('button', { name: 'Start microphone check' }).waitFor();
  await page.getByRole('button', { name: 'Start microphone check' }).click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(OUT_DIR, '02_mic_check_running.png') });
  await page.getByRole('button', { name: 'Stop microphone check' }).click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(OUT_DIR, '02_mic_check_done.png') });
  console.log('      Captured 02_mic_check.png');

  console.log('[3/6] Navigating to /signup (Adult Reader)...');
  await page.goto(base + '/signup');
  await page.getByRole('button', { name: 'Independent adult' }).click();
  const ts = Date.now();
  const username = `live_tester_${ts}`;
  await page.getByLabel('Your name', { exact: true }).fill('Paneer QA Tester');
  await page.getByLabel('Username', { exact: true }).fill(username);
  await page.getByLabel('Password', { exact: true }).fill('LiveTestPass123!');
  await page.screenshot({ path: path.join(OUT_DIR, '03_signup_form.png') });
  await page.getByRole('button', { name: 'Create My Account', exact: true }).click();
  await page.waitForSelector('text=Account created!');
  await page.screenshot({ path: path.join(OUT_DIR, '03_signup_success.png') });
  console.log('      Created adult user:', username);

  console.log('[4/6] Logging in and completing profile...');
  await page.getByRole('link', { name: 'Go to sign in' }).click();
  await page.getByLabel('Username', { exact: true }).waitFor();
  await page.getByLabel('Username', { exact: true }).fill(username);
  await page.getByLabel('Password', { exact: true }).fill('LiveTestPass123!');
  await page.getByRole('button', { name: 'Sign In', exact: true }).click();
  await page.waitForURL('**/profile');
  await page.getByLabel('Your native language', { exact: true }).waitFor();
  await page.getByLabel('Your native language', { exact: true }).selectOption('en');
  await page.screenshot({ path: path.join(OUT_DIR, '04_profile_setup.png') });
  await page.getByRole('button', { name: 'Save & continue' }).click();
  await page.waitForURL('**/home');
  await page.waitForSelector('text=No flagged words to show yet');
  await page.screenshot({ path: path.join(OUT_DIR, '05_reader_home.png'), fullPage: true });
  console.log('      Profile saved, reached Reader Home.');

  console.log('[5/6] Navigating to /bookshelf...');
  await page.goto(base + '/books');
  await page.waitForSelector('text=The Brave Little Fox');
  await page.screenshot({ path: path.join(OUT_DIR, '06_bookshelf.png'), fullPage: true });
  console.log('      Bookshelf loaded.');

  console.log('[6/6] Opening "The Brave Little Fox" Book Reader...');
  await page.goto(base + '/book/story_forest_01?lang=en');
  await page.getByRole('button', { name: 'Open this book', exact: true }).waitFor();
  await page.screenshot({ path: path.join(OUT_DIR, '07_book_cover.png') });
  await page.getByRole('button', { name: 'Open this book', exact: true }).click();
  await page.waitForSelector('text=The little fox woke up early in the morning.');
  await page.screenshot({ path: path.join(OUT_DIR, '08_book_reading_page1.png'), fullPage: true });
  console.log('      Book Reader ready on Page 1!');

  await browser.close();
  console.log('[BROWSER] All 6 journeys completed with zero errors!');
})();
