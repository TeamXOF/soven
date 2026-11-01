/* Real signup/approval HTTP and UI; synthetic accounts in the harness's private DB. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const base = process.env.VALIDATION_ENROLLMENT_URL;
  assert.ok(base && process.env.VALIDATION_TEACHER_PASSWORD, 'Run through validate_enrollment_runtime.py');
  const browser = await chromium.launch({ headless: true });
  const errors = [];
  const makePage = async () => {
    const context = await browser.newContext({ ignoreHTTPSErrors: true });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    return page;
  };
  const password = 'isolated-child-password';
  const login = async (page, username, secret) => {
    await page.goto(base + '/login');
    await page.getByPlaceholder('your username').fill(username);
    await page.locator('input[type=password]').fill(secret);
    const reply = page.waitForResponse(response => response.url().endsWith('/api/auth/login') && response.request().method() === 'POST');
    await page.getByRole('button', { name: 'Sign In', exact: true }).click();
    const response = await reply;
    return { status: response.status(), body: await response.json() };
  };
  const signup = async (page, name, username) => {
    await page.goto(base + '/signup');
    await page.getByPlaceholder('Ask your teacher for the code').fill('enrollment-ui-code');
    await page.getByPlaceholder('e.g. Ayaan Khan').fill(name);
    await page.getByPlaceholder('letters, numbers, . _ -').fill(username);
    await page.getByPlaceholder('at least 10 characters').fill(password);
    await page.getByRole('button', { name: 'Create My Account', exact: true }).click();
    await page.getByRole('heading', { name: 'Account created! 🎉' }).waitFor();
  };
  const approve = async (teacher, username, expectedId) => {
    // The wrapping label also contains the select's option text.
    const select = teacher.getByLabel('Student profile for @' + username);
    await select.waitFor();
    const card = select.locator('..').locator('..');
    const button = card.getByRole('button', { name: 'Approve', exact: true });
    if (expectedId) {
      assert.equal(await select.inputValue(), '', 'Same-name profile requires an explicit choice');
      assert.equal(await button.isDisabled(), true);
      await select.selectOption(expectedId);
    } else {
      assert.equal(await select.inputValue(), '__new__');
    }
    const reply = teacher.waitForResponse(response => response.url().endsWith('/approve') && response.request().method() === 'POST');
    await button.click();
    const response = await reply;
    assert.equal(response.status(), 200);
    const body = await response.json();
    assert.equal(body.created_profile, !expectedId);
    if (expectedId) assert.equal(body.student_id, expectedId);
    await select.waitFor({ state: 'detached' });
    await teacher.getByRole('row').filter({ hasText: '@' + username }).waitFor();
    return body.student_id;
  };
  try {
    const child = await makePage();
    await signup(child, 'New child', 'new-ui-child');
    assert.equal((await login(child, 'new-ui-child', password)).status, 403);
    const teacher = await makePage();
    assert.equal((await login(teacher, 'ui-teacher', process.env.VALIDATION_TEACHER_PASSWORD)).status, 200);
    await teacher.waitForURL('**/teacher');
    await teacher.goto(base + '/students');
    assert.equal(await teacher.getByTestId('classroom-signup-code').textContent(), 'enrollment-ui-code');
    const createdId = await approve(teacher, 'new-ui-child');
    const signedIn = await login(child, 'new-ui-child', password);
    assert.equal(signedIn.status, 200);
    assert.equal(signedIn.body.user.student_id, createdId);
    await child.waitForURL('**/dashboard');
    const existingChild = await makePage();
    await signup(existingChild, 'Existing child', 'existing-ui-child');
    await teacher.reload();
    await approve(teacher, 'existing-ui-child', 'existing-ui-profile');
    const existingLogin = await login(existingChild, 'existing-ui-child', password);
    assert.equal(existingLogin.status, 200);
    assert.equal(existingLogin.body.user.student_id, 'existing-ui-profile');
    await existingChild.waitForURL('**/dashboard');
    await teacher.goto(base + '/settings');
    await teacher.getByRole('heading', { name: 'Waiting for approval (0)', exact: true }).waitFor();
    assert.deepEqual(errors, []);
    const report = { success: true, scope: 'Isolated temporary database, real UI and HTTP, synthetic accounts only', checks: [
      'child signup remains pending and cannot log in', 'classroom code visible on Students page',
      'approval creates and links one new profile', 'approved child logs in with that profile',
      'same-name roster profile requires explicit selection', 'existing profile linked without a duplicate',
      'linked child logs in with existing profile', 'Settings shares the current approval queue', 'no browser runtime errors'
    ] };
    fs.writeFileSync(path.join(process.env.VALIDATION_ENROLLMENT_OUT, 'enrollment-results.json'), JSON.stringify(report, null, 2));
    process.stdout.write(JSON.stringify(report));
  } finally {
    await browser.close();
  }
})().catch(error => { process.stderr.write(error.stack); process.exitCode = 1; });
