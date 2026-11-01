/* UI-only scenarios with real isolated auth; fake microphone and controlled reading responses. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const base = process.env.VALIDATION_ENROLLMENT_URL;
  assert.ok(base && process.env.VALIDATION_TEACHER_PASSWORD, 'Run via the isolated runtime harness');
  const browser = await chromium.launch({ headless: true, args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'] });
  const context = await browser.newContext({ ignoreHTTPSErrors: true, permissions: ['microphone'], viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const checks = [];
  let mode = 'normal', requestCount = 0, releaseReading, releaseSentence, delayedSentence = false;
  let studentId, unauthorizedAfterRelease = false;
  const out = process.env.VALIDATION_ENROLLMENT_OUT;
  const until = async predicate => {
    for (let i = 0; i < 150; i++) {
      if (predicate()) return;
      await new Promise(resolve => setTimeout(resolve, 20));
    }
    throw new Error("Controlled request did not arrive");
  };
  const visible = (name) => page.getByRole('region', { name, exact: true });
  const waitText = async (locator, text) => {
    await locator.filter({ hasText: text }).waitFor();
  };
  const readingReply = (body) => {
    const ur = body.language === 'ur';
    const words = ur ? [
      { word: 'وہ', spoken: 'وہ', correct: true, phoneme_mismatch: null },
      { word: 'یہاں', spoken: 'وہاں', correct: false, phoneme_mismatch: 'word substitution' },
      { word: 'تھا', spoken: 'تھا', correct: true, phoneme_mismatch: null },
    ] : [
      { word: 'The', spoken: 'The', correct: true, phoneme_mismatch: null },
      { word: 'cat', spoken: 'dog', correct: false, phoneme_mismatch: 'word substitution' },
      { word: 'sat', spoken: 'sat', correct: true, phoneme_mismatch: null },
    ];
    if (mode === 'missing-extra') {
      words[1] = { word: 'cat', spoken: '', correct: false, phoneme_mismatch: null };
      words.push({ word: 'hello', spoken: 'hello', correct: false, extra: true, phoneme_mismatch: 'extra word' });
    }
    const diagnosis = {
      phonetic: { source: 'measured_alignment', status: 'available', struggling_words: [ur ? 'یہاں' : 'cat'] },
      engagement: { source: 'measured_alignment', status: 'available', teacher_note: ur ? 'ریکارڈنگ میں لمبے وقفے: 0۔' : 'Long gaps detected in the recording: 0.' },
      difficulty: { source: 'template_fallback', status: 'fallback', primary_issue: ur ? 'دکھائے گئے الفاظ آہستہ پڑھیں۔' : 'Read the words to review slowly, then try again.' },
      practice: { source: 'template_fallback', status: 'fallback', focus_area: ur ? 'الفاظ کی مشق' : 'Read again',
        encouraging_note: ur ? 'ہر لفظ آرام سے پڑھیں۔' : 'Take your time with each word.',
        sentences: [{ text: ur ? 'یہاں۔' : 'cat.', target_word: ur ? 'یہاں' : 'cat', difficulty: 'easy' }] },
      progress: { source: 'measured_history', status: 'unavailable', trend: 'insufficient_data',
        report_text: ur ? 'موازنہ کرنے کے لیے اسی زبان میں یہی جملہ دوبارہ پڑھیں۔' : 'Read this same sentence again in this language to compare word match.' },
    };
    if (mode === 'repeat-exercise') diagnosis.practice.sentences[0].text = body.target_sentence;
    if (mode === 'legacy') Object.values(diagnosis).forEach(block => { delete block.source; delete block.status; });
    return { session_id: 'simulated-ui-only-' + requestCount, transcript: ur ? 'وہ وہاں تھا' : 'The dog sat',
      overall_score: 67, accuracy: 67, wpm: 60, pauses: 0, words, words_spoken: words.filter(w => w.spoken).map((w, i) => ({
        word: w.spoken, start: i * .4, end: (i + 1) * .4, probability: .9,
      })), diagnosis };
  };
  await page.route('**/pipeline/sentences?**', async route => {
    const ur = new URL(route.request().url()).searchParams.get('language') === 'ur';
    if (delayedSentence && ur) await new Promise(resolve => { releaseSentence = resolve; });
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ sentences: [ur ? 'وہ یہاں تھا۔' : 'The cat sat.'], source: 'test-only' }) });
  });
  await page.route('**/pipeline/run', async route => {
    requestCount++;
    if (mode === 'deferred') await new Promise(resolve => { releaseReading = resolve; });
    if (unauthorizedAfterRelease) return route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ detail: 'Expired previous account' }) });
    if (mode === 'failure') return route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Synthetic retry failure' }) });
    const body = route.request().postDataJSON();
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(readingReply(body)) });
  });
  await page.route(/\/api\/sessions\/?\?student_id=/, route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([
    { id: 'en-1', student_id: studentId, student_name: 'Test child', timestamp: '2026-10-30 12:00:00', language: 'en', accuracy: 1, wpm: 70 },
    { id: 'en-2', student_id: studentId, student_name: 'Test child', timestamp: '2026-10-31 12:00:00', language: 'en', accuracy: .67, wpm: 60 },
    { id: 'ur-1', student_id: studentId, student_name: 'Test child', timestamp: '2026-10-31 12:05:00', language: 'ur', accuracy: .8, wpm: 50 },
  ]) }));
  const login = async (username) => {
    await page.goto(base + '/login?next=/dashboard');
    await page.getByPlaceholder('your username').fill(username);
    await page.locator('input[type=password]').fill('synthetic-child-password');
    await page.getByRole('button', { name: 'Sign In', exact: true }).click();
    await page.waitForURL('**/dashboard');
    await page.getByRole('button', { name: 'Start Session', exact: true }).waitFor();
  };
  const record = async () => {
    const before = requestCount;
    if (mode === 'deferred') releaseReading = undefined;
    const start = page.getByRole('button', { name: /^(Start Session|پڑھنا شروع کریں)$/ });
    await start.click();
    const stop = page.getByRole('button', { name: /^(Stop Recording & Review|ریکارڈنگ روکیں اور موازنہ کریں)$/ });
    await stop.waitFor();
    assert.equal(await page.getByRole('button', { name: 'Read in English', exact: true }).isDisabled(), true);
    assert.equal(await page.getByRole('button', { name: 'Read in Urdu', exact: true }).isDisabled(), true);
    await page.waitForTimeout(250);
    // A rapid duplicate click must still produce only one request.
    await stop.evaluate(button => { button.click(); button.click(); });
    await until(() => requestCount === before + 1);
  };
  try {
    const teacher = await context.request.post(base + '/api/auth/login', { data: { username: 'ui-teacher', password: process.env.VALIDATION_TEACHER_PASSWORD } });
    assert.equal(teacher.status(), 200);
    const teacherToken = (await teacher.json()).token;
    for (const username of ['dashboard-child', 'second-dashboard-child']) {
      assert.equal((await context.request.post(base + '/api/auth/register', { data: { username, name: 'Test child', password: 'synthetic-child-password', classroom_code: 'enrollment-ui-code' } })).status(), 200);
      const users = await (await context.request.get(base + '/api/auth/users', { headers: { Authorization: 'Bearer ' + teacherToken } })).json();
      const child = users.find(user => user.username === username);
      const approved = await context.request.post(base + '/api/auth/users/' + child.id + '/approve', { headers: { Authorization: 'Bearer ' + teacherToken }, data: {} });
      assert.equal(approved.status(), 200);
      if (username === 'dashboard-child') studentId = (await approved.json()).student_id;
    }
    await login('dashboard-child');
    await visible('Your Reading').getByText('Read a sentence to see your word match and words to review.', { exact: true }).waitFor();
    assert.equal(await visible('Your Reading').locator('[class*="blur"]').count(), 0);
    assert.equal(await page.getByText('Multi-Agent Diagnosis', { exact: true }).count(), 0);
    checks.push('clear idle panels without blur or diagnostic labels');
    await page.waitForFunction(() => document.querySelectorAll('circle.recharts-dot').length === 4);
    checks.push('chart filters two English readings from mixed-language history');

    mode = 'deferred';
    const before = requestCount;
    await record();
    await waitText(visible('Practice & Feedback'), 'Preparing feedback…');
    assert.equal(await page.getByRole('button', { name: 'Processing…', exact: true }).isDisabled(), true);
    assert.equal(requestCount, before + 1);
    releaseReading();
    await page.getByTestId('reading-word-match').waitFor();
    await waitText(visible('Your Reading'), 'Reading complete · saved');
    await waitText(visible('Your Reading'), 'cat');
    await waitText(visible('Your Reading'), 'dog');
    await waitText(visible('Practice & Feedback'), 'Basic guidance');
    assert.equal(await page.getByText('Trend: insufficient_data', { exact: true }).count(), 0);
    assert.equal(await page.locator('.fixed.bottom-6.right-6').count(), 0);
    checks.push('recording and processing lock controls; duplicate stop submits once');
    checks.push('completed word comparisons, fallback guidance and friendly progress text');
    await page.screenshot({ path: path.join(out, 'dashboard-english.png'), fullPage: true });

    await visible('Targeted Practice').getByRole('button', { name: /cat\./ }).click();
    await page.getByRole('button', { name: 'Read This One Next', exact: true }).click();
    assert.equal(await page.getByTestId('reading-word-match').count(), 0);
    await page.getByRole('combobox', { name: 'Reading sentence', exact: true }).waitFor();
    assert.equal(await page.getByRole('combobox', { name: 'Reading sentence', exact: true }).inputValue(), 'cat.');
    checks.push('exercise becomes next target and clears the previous result');
    await page.getByRole('combobox', { name: 'Reading sentence', exact: true }).selectOption('The cat sat.');

    mode = 'failure';
    await record();
    await visible('Page notifications').getByRole('alert').filter({ hasText: 'Synthetic retry failure' }).waitFor();
    assert.equal(await visible('Page notifications').getByRole('alert').evaluate(element => getComputedStyle(element).position), 'static');
    await page.getByRole('button', { name: 'Dismiss message', exact: true }).click();
    assert.equal(await visible('Page notifications').getByRole('alert').count(), 0);
    await page.getByRole('button', { name: 'Notifications', exact: true }).click();
    await page.getByText('Synthetic retry failure', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Notifications', exact: true }).click();
    await page.getByRole('link', { name: 'Settings', exact: true }).click();
    await page.waitForURL('**/settings');
    await page.getByRole('link', { name: 'Sentence practice', exact: true }).click();
    await page.waitForURL('**/dashboard');
    await page.getByRole('button', { name: 'Start Session', exact: true }).waitFor();
    assert.equal(await visible('Page notifications').getByRole('alert').count(), 0);
    checks.push('failure visible inline; dismissal survives bell reads and navigation');

    mode = 'legacy';
    await record();
    await waitText(visible('Practice & Feedback'), 'Older result · source unknown');
    assert.equal(await visible('Page notifications').getByRole('alert').count(), 0);
    checks.push('new updates do not resurrect dismissed alerts; legacy sources remain unknown');
    await page.getByRole('button', { name: 'New Session', exact: true }).click();
    mode = 'repeat-exercise';
    await record();
    await page.getByTestId('reading-word-match').waitFor();
    await visible('Targeted Practice').getByRole('button', { name: /The cat sat\./ }).click();
    await page.getByRole('button', { name: 'Read This One Next', exact: true }).click();
    assert.equal(await page.getByTestId('reading-word-match').count(), 0);
    checks.push('repeating the same exercise also starts a clean session');
    mode = 'missing-extra';
    await record();
    await page.getByTestId('reading-word-match').waitFor();
    await waitText(visible('Your Reading'), 'Not recognized');
    await waitText(visible('Your Reading'), '(extra word)');
    checks.push('missing and extra recognized words appear in review');

    await page.getByRole('button', { name: 'New Session', exact: true }).click();
    mode = 'normal';
    delayedSentence = true;
    await page.getByRole('button', { name: 'Read in Urdu', exact: true }).click();
    await until(() => !!releaseSentence);
    await page.getByRole('button', { name: 'Read in English', exact: true }).click();
    await page.waitForFunction(() => document.querySelector('select[aria-label="Reading sentence"]')?.value === 'The cat sat.');
    releaseSentence();
    await page.waitForTimeout(150);
    assert.equal(await page.getByRole('combobox', { name: 'Reading sentence', exact: true }).inputValue(), 'The cat sat.');
    checks.push('late sentence response cannot overwrite a newer language selection');
    delayedSentence = false;
    await page.getByRole('button', { name: 'Read in Urdu', exact: true }).click();
    await page.waitForFunction(() => document.querySelector('select[aria-label="Reading sentence"]')?.value === 'وہ یہاں تھا۔');
    await record();
    await page.getByTestId('reading-word-match').waitFor();
    assert.equal(await visible('Your Reading').locator('[dir="rtl"]').count(), 1);
    await waitText(visible('Your Reading'), 'یہاں');
    await waitText(visible('Your Reading'), 'وہاں');
    await waitText(visible('Practice & Feedback'), 'بنیادی رہنمائی');
    await page.waitForFunction(() => document.querySelectorAll('circle.recharts-dot').length === 2);
    await page.screenshot({ path: path.join(out, 'dashboard-urdu.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('navigation', { name: 'Mobile navigation', exact: true }).waitFor();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    assert.equal(await page.locator('main').evaluate(element => element.scrollWidth <= element.clientWidth), true);
    await page.screenshot({ path: path.join(out, 'dashboard-urdu-mobile.png'), fullPage: true });
    await visible('Practice & Feedback').scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(out, 'dashboard-feedback-mobile.png'), fullPage: true });
    checks.push('Urdu feedback and exercises use RTL; chart filters Urdu; narrow layout fits');

    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.getByRole('button', { name: 'نئی ریکارڈنگ', exact: true }).click();
    await page.getByRole('button', { name: 'Read in English', exact: true }).click();
    mode = 'deferred';
    unauthorizedAfterRelease = true;
    await record();
    await waitText(visible('Practice & Feedback'), 'Preparing feedback…');
    await page.getByRole('button', { name: 'Log out', exact: true }).click();
    await page.waitForURL(/\/login(?:\?.*)?$/);
    await login('second-dashboard-child');
    releaseReading();
    await page.waitForTimeout(300);
    assert.equal(await page.getByTestId('reading-word-match').count(), 0);
    assert.equal(await visible('Page notifications').getByRole('alert').count(), 0);
    assert.equal(await page.evaluate(() => JSON.parse(localStorage.getItem('sf_user')).username), 'second-dashboard-child');
    checks.push('late unauthorized response cannot populate or log out the next account');
    assert.deepEqual(errors, []);
    const report = { success: true, scope: 'UI scenarios: synthetic accounts, isolated real auth, fake microphone, controlled reading responses; no physical speech-quality claim', checks, browser_runtime_errors: errors };
    fs.writeFileSync(path.join(out, 'dashboard-results.json'), JSON.stringify(report, null, 2));
    process.stdout.write(JSON.stringify(report));
  } catch (error) {
    await page.screenshot({ path: path.join(out, 'dashboard-failure.png'), fullPage: true }).catch(() => {});
    process.stderr.write(JSON.stringify({ stage: checks, body: (await page.locator('body').innerText()).slice(-4500) }) + '\n');
    throw error;
  } finally {
    if (releaseReading) releaseReading();
    if (releaseSentence) releaseSentence();
    await browser.close();
  }
})().catch(error => { process.stderr.write(error.stack); process.exitCode = 1; });
