# Test Results Dashboard

**Last Updated**: {ISO_8601_TIMESTAMP}
**Phase**: {PHASE} (Prototype | Development | Pre-deployment)

---

## Coverage Summary

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Reported Coverage | ≥{THRESHOLD}% | {REPORTED_COV}% | {STATUS} |
| Effective Coverage | - | {EFFECTIVE_COV}% | ℹ️ |
| Pass Rate | ≥{THRESHOLD}% | {PASS_RATE}% | {STATUS} |
| Fail Rate | 0% | {FAIL_RATE}% | {STATUS} |

---

## Test Results by Type

### Unit Tests
- **Total**: {UNIT_TOTAL} tests
- **Passed**: {UNIT_PASSED} ({UNIT_PASS_PCT}%)
- **Failed**: {UNIT_FAILED} ({UNIT_FAIL_PCT}%)
- **Duration**: {UNIT_DURATION}s
- **Coverage**: {UNIT_COVERAGE}%

### Integration Tests
- **Total**: {INTEGRATION_TOTAL} tests
- **Passed**: {INTEGRATION_PASSED} ({INTEGRATION_PASS_PCT}%)
- **Failed**: {INTEGRATION_FAILED} ({INTEGRATION_FAIL_PCT}%)
- **Duration**: {INTEGRATION_DURATION}s
- **Coverage**: {INTEGRATION_COVERAGE}%

### E2E Tests
- **Total**: {E2E_TOTAL} scenarios
- **Passed**: {E2E_PASSED} ({E2E_PASS_PCT}%)
- **Concessioned**: {E2E_CONCESSIONED} ({E2E_CONCESSION_PCT}%)
- **Failed**: {E2E_FAILED} ({E2E_FAIL_PCT}%)
- **Status**: {E2E_STATUS}

### Security Tests
- **Critical Issues**: {SECURITY_CRITICAL}
- **High Issues**: {SECURITY_HIGH}
- **Medium Issues**: {SECURITY_MEDIUM}
- **Low Issues**: {SECURITY_LOW}
- **Status**: {SECURITY_STATUS}

---

## Concessioned Tests

| ID | Type | Reason | Ticket | Age (days) |
|----|------|--------|--------|------------|
| {TEST_ID} | {TYPE} | {REASON} | #{TICKET} | {AGE} |

_No concessioned tests_ (if empty)

---

## Failed Tests

| ID | Type | Error | First Seen |
|----|------|-------|------------|
| {TEST_ID} | {TYPE} | {ERROR_MSG} | {TIMESTAMP} |

_No failed tests_ ✅ (if empty)

---

## Trends (Last 7 Days)

- **Coverage**: {COVERAGE_7D_AGO}% → {COVERAGE_NOW}% ({COVERAGE_DELTA})
- **Pass Rate**: {PASS_RATE_7D_AGO}% → {PASS_RATE_NOW}% ({PASS_RATE_DELTA})
- **Test Count**: {TEST_COUNT_7D_AGO} → {TEST_COUNT_NOW} ({TEST_COUNT_DELTA})
- **E2E Scenarios**: {E2E_COUNT_7D_AGO} → {E2E_COUNT_NOW} ({E2E_COUNT_DELTA})

---

## Recent Test Runs

| Date | Phase | Coverage | Pass Rate | Duration | Status |
|------|-------|----------|-----------|----------|--------|
| {DATE} | {PHASE} | {COV}% | {PASS}% | {DUR}s | {STATUS} |

---

## Notes

- Auto-generated from test run at {TIMESTAMP}
- Dashboard template: `context/templates/test-dashboard-template.md`
- Update this file after each test run (unit, integration, e2e, security)
