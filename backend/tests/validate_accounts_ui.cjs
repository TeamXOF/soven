/* Real HTTP/profile storage plus the unchanged sign-in UI; synthetic data only. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const base = process.env.VALIDATION_ENROLLMENT_URL;
  assert.ok(base, 'Run through validate_enrollment_runtime.py');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();
  const errors = [];
  const checks = [];
  const responses = [];
  page.on('response', response => { const url = new URL(response.url()); if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/pipeline')) responses.push({ path: url.pathname, status: response.status() }); });
  page.on('pageerror', error => errors.push(error.message));
  try {
    const password = 'isolated-adult-password';
    let response = await context.request.post(base + '/api/auth/register-adult', {
      data: { name: 'Independent reader', username: 'adult-ui-reader', password },
    });
    assert.equal(response.status(), 201);
    checks.push('adult API registration succeeds without a classroom code');
    await page.goto(base + '/login');
    await page.getByPlaceholder('your username').fill('adult-ui-reader');
    await page.locator('input[type=password]').fill(password);
    const reply = page.waitForResponse(r => r.url().endsWith('/api/auth/login') && r.request().method() === 'POST');
    await page.getByRole('button', { name: 'Sign In', exact: true }).click();
    response = await reply;
    assert.equal(response.status(), 200);
    const login = await response.json();
    assert.equal(login.user.reader_mode, 'adult');
    assert.equal(login.user.account_scope, 'personal');
    assert.equal(login.user.is_admin, 0);
    await page.waitForURL('**/dashboard');
    await page.getByRole('heading', { name: 'Reading Session Dashboard', exact: true }).waitFor();
    checks.push('unchanged sign-in UI accepts the adult reader with no teacher privileges');
    const headers = { Authorization: 'Bearer ' + login.token };
    response = await context.request.get(base + '/api/students/', { headers });
    const own = await response.json();
    assert.deepEqual(own.map(row => row.id), [login.user.student_id]);
    response = await context.request.get(base + '/api/students/existing-ui-profile', { headers });
    assert.equal(response.status(), 403);
    checks.push('adult roster contains only its reader; existing school data is inaccessible');
    response = await context.request.patch(base + '/api/auth/profile', {
      headers, data: { expected_version: 1, reading_language: 'ur', interface_language: 'en',
        native_language: 'fr', translation_language: 'es', accessibility: { larger_text: true }, complete_profile: true },
    });
    assert.equal(response.status(), 200);
    assert.equal((await response.json()).profile.version, 2);
    await page.reload();
    await page.getByRole('heading', { name: 'Reading Session Dashboard' }).waitFor();
    response = await context.request.get(base + '/api/auth/me', { headers });
    const user = (await response.json()).user;
    assert.equal(user.profile.reading_language, 'ur');
    assert.equal(user.profile.interface_language, 'en');
    assert.equal(user.profile.native_language, 'fr');
    assert.equal(user.profile.translation_language, 'es');
    assert.equal(user.profile.profile_completed, true);
    checks.push('four language preferences and completion persist through real HTTP and page reload');
    response = await context.request.patch(base + '/api/auth/profile', {
      headers, data: { expected_version: 1, native_language: 'de' },
    });
    assert.equal(response.status(), 409);
    checks.push('stale profile saves return a conflict');
    response = await context.request.get(base + '/api/auth/users', { headers });
    assert.equal(response.status(), 403);
    assert.deepEqual(errors, []);
    checks.push('teacher account management remains forbidden; no browser runtime errors');
    const report = { success: true, scope: 'Isolated adult/profile API integration through real HTTP and unchanged login UI; no redesigned screens, real microphone or provider calls', checks, browser_runtime_errors: errors };
    fs.writeFileSync(path.join(process.env.VALIDATION_ENROLLMENT_OUT, 'accounts-results.json'), JSON.stringify(report, null, 2));
    process.stdout.write(JSON.stringify(report));
  } catch (error) {
    await page.screenshot({ path: path.join(process.env.VALIDATION_ENROLLMENT_OUT, 'accounts-failure.png'), fullPage: true });
    process.stderr.write(JSON.stringify({ url: page.url(), body: (await page.locator('body').innerText()).slice(0, 2500), browser_errors: errors, responses, has_stored_token: await page.evaluate(() => !!localStorage.getItem('sf_token')) }));
    throw error;
  } finally {
    await browser.close();
  }
})().catch(error => { process.stderr.write(error.stack); process.exitCode = 1; });
