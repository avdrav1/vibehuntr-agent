# Manual Testing Quick Start Guide

**Time Required:** 40-120 minutes
**Prerequisites:** Basic familiarity with web applications

---

## Step 1: Environment Setup (5 minutes)

### Check Configuration

```bash
# Navigate to project directory
cd /path/to/vibehuntr-agent

# Verify environment variables
cat .env | grep -E "GOOGLE_API_KEY|USE_DOCUMENT_RETRIEVAL"
```

**Required Variables:**
- `GOOGLE_API_KEY` - Your Gemini API key
- `USE_DOCUMENT_RETRIEVAL` - Set to `true` or `false`

### Install Dependencies (if needed)

```bash
make install
```

### Verify Automated Tests Pass

```bash
make test
```

**Expected:** All tests should pass (170+ tests)

---

## Step 2: Start the Playground (1 minute)

```bash
./start_playground.sh
```

**Or:**

```bash
streamlit run vibehuntr_playground.py
```

**Expected:** Browser opens to `http://localhost:8501`

---

## Step 3: Quick Smoke Test (5 minutes)

### Test 1: Basic Interaction
1. Type: "Hello"
2. Press Enter
3. **Verify:** Agent responds with a greeting

### Test 2: Tool Invocation
1. Type: "Create a user named Test User with email test@example.com"
2. **Verify:** Agent creates user and returns ID

### Test 3: Visual Check
- **Verify:** Vibehuntr logo (🎉) visible
- **Verify:** Purple/pink gradient colors
- **Verify:** Dark theme applied
- **Verify:** Messages styled correctly

**If all 3 tests pass, continue to full testing.**

---

## Step 4: Full Testing (30-90 minutes)

### Option A: Quick Checklist (40 minutes)

Open and follow: **`MANUAL_TESTING_CHECKLIST.md`**

This provides a rapid checklist covering all critical functionality.

### Option B: Comprehensive Testing (90 minutes)

Open and follow: **`MANUAL_TESTING_GUIDE.md`**

This provides detailed test scenarios with step-by-step instructions.

---

## Step 5: Record Results

### Quick Recording

Use the template in `MANUAL_TESTING_CHECKLIST.md`:

```markdown
**Date:** [Today's date]
**Tester:** [Your name]
**Status:** ✅ PASS / ❌ FAIL

**Issues Found:**
1. [Description]
2. [Description]
```

### Detailed Recording

Use the template in `MANUAL_TESTING_GUIDE.md`:

```markdown
## Test Session: [Date/Time]

**Configuration:**
- Agent Type: [Simple/Full]
- Browser: [Chrome/Firefox/Safari/Edge]
- Screen Size: [Desktop/Laptop/Tablet/Mobile]

### Test Results:
[Complete table with all test scenarios]
```

---

## Common Test Scenarios

### Scenario 1: Event Planning Flow

```
1. "Create a user named Alice"
2. "Create a group called Birthday Party"
3. "Add Alice to the Birthday Party group"
4. "Help me plan a birthday party for 10 people"
```

**Verify:** All commands execute successfully

### Scenario 2: Venue Search

```
1. "Find restaurants in San Francisco"
2. "Show me only vegetarian options"
3. "Tell me more about [venue name from results]"
```

**Verify:** Places API returns results

### Scenario 3: History Pagination

```
1. Send 15 short messages (e.g., "Message 1", "Message 2", ...)
2. Verify only last 10 visible
3. Click "Show Older Messages"
4. Verify older messages appear
```

**Verify:** Pagination works correctly

### Scenario 4: Error Handling

```
1. Send a message that might cause an error
2. Verify error message is user-friendly
3. Verify application doesn't crash
4. Verify you can continue conversation
```

**Verify:** Graceful error handling

---

## What to Look For

### ✅ Good Signs

- Responses appear within 1-2 seconds
- Streaming is smooth (no long pauses)
- Branding is consistent throughout
- Errors are user-friendly
- UI is responsive and doesn't freeze
- Tools execute successfully
- Context is maintained across messages

### ❌ Red Flags

- Application crashes
- Long delays (>10 seconds) without feedback
- Styling is broken or inconsistent
- Error messages show stack traces
- Tools fail to execute
- Context is lost between messages
- UI becomes unresponsive

---

## Troubleshooting

### Issue: Playground won't start

**Solution:**
```bash
# Check if port 8501 is in use
lsof -i :8501

# Kill the process if needed
kill -9 [PID]

# Restart
./start_playground.sh
```

### Issue: Agent not responding

**Solution:**
1. Check `.env` file has `GOOGLE_API_KEY`
2. Verify API key is valid
3. Check internet connection
4. Look at terminal for error messages

### Issue: Styling looks wrong

**Solution:**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+Shift+R)
3. Try incognito/private mode

### Issue: Tools not working

**Solution:**
1. Check agent configuration
2. Verify `USE_DOCUMENT_RETRIEVAL` setting
3. Check logs in terminal

---

## Reporting Issues

### Critical Issues (Report Immediately)

- Application crashes
- Agent doesn't respond at all
- Major security concerns
- Data loss

### Non-Critical Issues (Document for Later)

- Minor styling inconsistencies
- Slow performance (but functional)
- Unclear error messages
- UI/UX improvements

### Issue Report Format

```markdown
**Issue:** [Brief description]
**Severity:** Critical / High / Medium / Low
**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected:** [What should happen]
**Actual:** [What actually happened]
**Screenshot:** [If applicable]
**Browser:** [Chrome/Firefox/etc.]
**Date:** [Date found]
```

---

## Success Criteria

### Minimum Requirements (Must Pass)

- ✅ Agent responds to messages
- ✅ Basic conversation flow works
- ✅ At least one tool invocation succeeds
- ✅ Branding is visible and correct
- ✅ No crashes during normal use

### Full Success (All Should Pass)

- ✅ All test scenarios complete successfully
- ✅ Responsive design works on multiple screen sizes
- ✅ Error handling is graceful
- ✅ Performance is acceptable
- ✅ Context is maintained
- ✅ History pagination works
- ✅ New conversation functionality works

---

## After Testing

### If All Tests Pass ✅

1. Complete the sign-off in `TESTING_SUMMARY.md`
2. Document any minor issues found
3. Approve for production deployment

### If Critical Issues Found ❌

1. Document all issues clearly
2. Prioritize by severity
3. Report to development team
4. Re-test after fixes

---

## Questions?

- **Setup Issues:** See `PLAYGROUND_GUIDE.md`
- **Detailed Testing:** See `MANUAL_TESTING_GUIDE.md`
- **Quick Reference:** See `MANUAL_TESTING_CHECKLIST.md`
- **Test Status:** See `TESTING_SUMMARY.md`

---

## Ready to Start?

1. ✅ Environment configured
2. ✅ Dependencies installed
3. ✅ Automated tests passing
4. ✅ Playground started
5. ✅ This guide open

**Let's begin testing! 🎉**

Start with the Quick Smoke Test (Step 3) above, then proceed to full testing (Step 4).

Good luck! 🚀
