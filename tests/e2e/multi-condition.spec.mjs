import { chromium } from 'playwright';

const BASE = 'http://localhost:5174';
let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) {
    console.log(`  PASS: ${msg}`);
    passed++;
  } else {
    console.log(`  FAIL: ${msg}`);
    failed++;
  }
}

async function run() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.setDefaultTimeout(30000);

  // ============================================================
  // TEST 1: Single-condition simulation (backward compat)
  // ============================================================
  console.log('\n=== Test 1: Single-condition simulation ===');
  await page.goto(BASE);

  // Verify initial page loads
  const title = await page.textContent('h1');
  assert(title === 'AO Simulator', 'Page title renders');

  // Verify multi-condition checkbox exists and is unchecked
  const mcCheckbox = page.locator('input[type="checkbox"]');
  assert(await mcCheckbox.count() > 0, 'Multi-condition checkbox exists');
  assert(!(await mcCheckbox.first().isChecked()), 'Multi-condition unchecked by default');

  // Verify schedule config is visible
  const schedSection = page.locator('.schedule-input');
  assert(await schedSection.count() >= 2, 'Schedule A and B inputs visible in single mode');

  // Run a single-condition simulation
  await page.click('.run-btn');
  await page.waitForSelector('.results-page', { timeout: 30000 });

  const resultsTitle = await page.textContent('.results-page h1');
  assert(resultsTitle === 'Simulation Results', 'Results page renders');

  // Verify cumulative record chart renders
  const chartContainer = page.locator('.chart-container');
  assert(await chartContainer.count() === 1, 'Cumulative record chart renders');

  // Verify chart has SVG (recharts renders SVG)
  const chartSvg = chartContainer.locator('svg');
  assert(await chartSvg.count() >= 1, 'Chart contains SVG element');

  // Verify NO condition breakdown table for single condition
  const condBreakdown = page.locator('.condition-breakdown');
  assert(await condBreakdown.count() === 0, 'No condition breakdown for single condition');

  // Verify download buttons exist
  const downloadBtns = page.locator('.download-section button');
  assert(await downloadBtns.count() === 2, 'CSV and JSON download buttons present');

  // Go back
  await page.click('.back-btn');
  await page.waitForSelector('.config-page');

  // ============================================================
  // TEST 2: Multi-condition toggle + editor
  // ============================================================
  console.log('\n=== Test 2: Multi-condition toggle and editor ===');

  // Enable multi-condition
  await mcCheckbox.first().check();
  assert(await mcCheckbox.first().isChecked(), 'Multi-condition checkbox checked');

  // Verify condition editor appears
  const condCards = page.locator('.condition-card');
  assert(await condCards.count() === 1, 'One condition card seeded on toggle');

  // Verify schedule config is hidden when multi-condition is on
  // The ScheduleConfig component section should be replaced by ConditionEditor
  const condEditor = page.locator('.condition-list');
  assert(await condEditor.count() === 1, 'Condition editor visible');

  // Verify the seeded condition has label
  const labelInput = condCards.first().locator('input[type="text"]');
  const labelVal = await labelInput.inputValue();
  assert(labelVal === 'Condition 1', 'First condition label seeded');

  // Add a second condition
  await page.click('.condition-add-btn');
  assert(await condCards.count() === 2, 'Second condition added');

  // Add a third condition
  await page.click('.condition-add-btn');
  assert(await condCards.count() === 3, 'Third condition added');

  // ============================================================
  // TEST 3: Edit condition labels and schedules
  // ============================================================
  console.log('\n=== Test 3: Edit conditions ===');

  // Edit first condition label
  const labels = page.locator('.condition-card input[type="text"]');
  await labels.nth(0).fill('Baseline');
  assert(await labels.nth(0).inputValue() === 'Baseline', 'First condition label edited');

  await labels.nth(1).fill('Reversal');
  assert(await labels.nth(1).inputValue() === 'Reversal', 'Second condition label edited');

  await labels.nth(2).fill('Extinction');
  assert(await labels.nth(2).inputValue() === 'Extinction', 'Third condition label edited');

  // Edit max_steps for each condition via the number inputs inside each card
  // Each card has: max_steps input, then schedule value inputs
  const card1Steps = condCards.nth(0).locator('input[type="number"]').first();
  await card1Steps.fill('300');

  const card2Steps = condCards.nth(1).locator('input[type="number"]').first();
  await card2Steps.fill('300');

  const card3Steps = condCards.nth(2).locator('input[type="number"]').first();
  await card3Steps.fill('200');

  // ============================================================
  // TEST 4: Run 3-condition experiment
  // ============================================================
  console.log('\n=== Test 4: Run 3-condition experiment ===');

  await page.click('.run-btn');
  await page.waitForSelector('.results-page', { timeout: 60000 });

  // Verify cumulative record chart
  const chart2 = page.locator('.chart-container');
  assert(await chart2.count() === 1, 'Cumulative record chart renders for multi-condition');

  // Verify chart has reference lines for condition boundaries
  // Recharts renders ReferenceLine as <line> elements with stroke-dasharray
  const chartSvg2 = chart2.locator('svg');
  assert(await chartSvg2.count() >= 1, 'Chart SVG renders');

  // Verify condition breakdown table appears
  const breakdown = page.locator('.condition-breakdown');
  assert(await breakdown.count() === 1, 'Condition breakdown table renders');

  // Verify breakdown has 3 data rows
  const breakdownRows = breakdown.locator('tbody tr');
  assert(await breakdownRows.count() === 3, 'Breakdown has 3 condition rows');

  // Verify total steps shown in summary
  const summaryText = await page.textContent('.summary');
  assert(summaryText.includes('800'), 'Total steps = 800 (300+300+200)');

  // Verify action count chips appear
  const chips = page.locator('.action-count-chip');
  assert(await chips.count() > 0, 'Action count chips render in breakdown');

  // Go back
  await page.click('.back-btn');
  await page.waitForSelector('.config-page');

  // ============================================================
  // TEST 5: Condition add/remove limits
  // ============================================================
  console.log('\n=== Test 5: Condition add/remove limits ===');

  // Re-enable multi-condition (state resets on back navigation)
  await mcCheckbox.first().check();
  await page.waitForSelector('.condition-card');

  // Add up to 6
  while (await page.locator('.condition-card').count() < 6) {
    await page.click('.condition-add-btn');
  }
  assert(await page.locator('.condition-card').count() === 6, 'Can add up to 6 conditions');

  // Verify add button disappears at 6
  const addBtn = page.locator('.condition-add-btn');
  assert(await addBtn.count() === 0, 'Add button hidden at max 6 conditions');

  // Remove conditions down to 1
  while (await page.locator('.condition-card').count() > 1) {
    await page.locator('.condition-remove-btn').first().click();
  }
  assert(await page.locator('.condition-card').count() === 1, 'Can remove down to 1 condition');

  // Verify remove button is gone when only 1 condition
  const removeBtn = page.locator('.condition-remove-btn');
  assert(await removeBtn.count() === 0, 'Remove button hidden at min 1 condition');

  // ============================================================
  // TEST 6: Toggle off returns to single mode
  // ============================================================
  console.log('\n=== Test 6: Toggle off returns to single mode ===');

  await mcCheckbox.first().uncheck();
  assert(!(await mcCheckbox.first().isChecked()), 'Multi-condition unchecked');

  // Verify condition editor gone, schedule config back
  assert(await page.locator('.condition-list').count() === 0, 'Condition editor hidden');
  assert(await page.locator('.schedule-input').count() >= 2, 'Schedule inputs visible again');

  // Max steps field should be back (2 labels: Max Steps + Seed)
  const paramLabels = await page.locator('.param-grid label').count();
  assert(paramLabels >= 2, `Max steps and seed fields visible (found ${paramLabels})`);

  // ============================================================
  // TEST 7: Grid chamber multi-condition
  // ============================================================
  console.log('\n=== Test 7: Grid chamber multi-condition ===');

  // Switch to grid_chamber
  await page.locator('select').first().selectOption('grid_chamber');
  await page.waitForTimeout(500);

  // Enable multi-condition (may already be checked, so uncheck first then check)
  const isChecked = await mcCheckbox.first().isChecked();
  if (isChecked) {
    await mcCheckbox.first().uncheck();
    await page.waitForTimeout(300);
  }
  await mcCheckbox.first().click();
  await page.waitForSelector('.condition-card');

  // Should see single schedule (not A/B) in condition card
  const gridCondCards = page.locator('.condition-card');
  assert(await gridCondCards.count() >= 1, 'Condition card exists for grid');

  // Each grid condition card should have 1 schedule input (not 2)
  const gridSchedInputs = gridCondCards.first().locator('.schedule-input');
  assert(await gridSchedInputs.count() === 1, 'Grid condition has single schedule input');

  // Add second condition and run
  await page.click('.condition-add-btn');
  await page.click('.run-btn');
  await page.waitForSelector('.results-page', { timeout: 60000 });

  const gridChart = page.locator('.chart-container');
  assert(await gridChart.count() === 1, 'Grid cumulative record chart renders');

  const gridBreakdown = page.locator('.condition-breakdown');
  assert(await gridBreakdown.count() === 1, 'Grid condition breakdown renders');

  // Go back for next tests
  await page.click('.back-btn');
  await page.waitForSelector('.config-page');

  // ============================================================
  // TEST 8: All 3 algorithms x 2 environments (6 combos)
  // ============================================================
  console.log('\n=== Test 8: All algo/env combos ===');

  const algos = ['q_learning', 'etbd', 'mpr'];
  const envs = ['two_choice', 'grid_chamber'];

  for (const env of envs) {
    for (const algo of algos) {
      await page.goto(BASE);
      await page.waitForSelector('.config-page');

      // Select environment
      const envSelect = page.locator('select').first();
      await envSelect.selectOption(env);

      // Select algorithm
      const algoSelect = page.locator('select').nth(1);
      await algoSelect.selectOption(algo);

      // Run
      await page.click('.run-btn');
      await page.waitForSelector('.results-page', { timeout: 60000 });

      const hasChart = await page.locator('.chart-container').count();
      assert(hasChart === 1, `${algo}/${env}: results page renders`);

      await page.click('.back-btn');
      await page.waitForSelector('.config-page');
    }
  }

  // ============================================================
  // TEST 9: CSV download content verification
  // ============================================================
  console.log('\n=== Test 9: CSV download verification ===');

  const csvReq = {
    environment: 'two_choice',
    algorithm: 'q_learning',
    max_steps: 20,
    seed: 42,
    schedule_a: { type: 'FR', value: 5 },
    schedule_b: { type: 'FR', value: 5 },
  };

  const csvResp = await page.evaluate(async (body) => {
    const res = await fetch('/api/simulate/csv', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return { ok: res.ok, contentType: res.headers.get('content-type'), text: await res.text() };
  }, csvReq);

  assert(csvResp.ok, 'CSV endpoint returns OK');
  assert(csvResp.contentType.includes('text/csv'), 'CSV content-type is text/csv');

  const csvLines = csvResp.text.trim().split('\n');
  assert(csvLines[0].includes('step'), 'CSV header has step column');
  assert(csvLines[0].includes('action'), 'CSV header has action column');
  assert(csvLines.length === 21, `CSV has header + 20 rows (got ${csvLines.length})`);

  // ============================================================
  // TEST 10: JSON download content verification
  // ============================================================
  console.log('\n=== Test 10: JSON download verification ===');

  const jsonReq = { ...csvReq };
  const jsonResp = await page.evaluate(async (body) => {
    const res = await fetch('/api/simulate/json', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return { ok: res.ok, contentType: res.headers.get('content-type'), text: await res.text() };
  }, jsonReq);

  assert(jsonResp.ok, 'JSON endpoint returns OK');
  assert(jsonResp.contentType.includes('application/json'), 'JSON content-type correct');

  const jsonData = JSON.parse(jsonResp.text);
  assert('config' in jsonData, 'JSON has config key');
  assert('summary' in jsonData, 'JSON has summary key');
  assert('steps' in jsonData, 'JSON has steps key');
  assert(jsonData.steps.length === 20, `JSON has 20 steps (got ${jsonData.steps.length})`);

  // ============================================================
  // TEST 11: Error handling (missing required fields)
  // ============================================================
  console.log('\n=== Test 11: Error handling ===');

  const errResp = await page.evaluate(async () => {
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    return { status: res.status };
  });

  assert(errResp.status === 422, `Empty request returns 422 (got ${errResp.status})`);

  // ============================================================
  // SUMMARY
  // ============================================================
  await browser.close();

  console.log(`\n${'='.repeat(50)}`);
  console.log(`RESULTS: ${passed} passed, ${failed} failed, ${passed + failed} total`);
  console.log('='.repeat(50));

  process.exit(failed > 0 ? 1 : 0);
}

run().catch(err => {
  console.error('Test runner error:', err);
  process.exit(1);
});
