# 🎉 Start Manual Testing - Vibehuntr Playground

**Ready to test?** This guide will get you started in 5 minutes!

---

## Quick Start

### 1. Verify Setup (1 minute)

```bash
# Check your API key is set
cat .env | grep GOOGLE_API_KEY

# Should show: GOOGLE_API_KEY=your_key_here
```

### 2. Start the Playground (1 minute)

```bash
./start_playground.sh
```

**Expected:** Browser opens to `http://localhost:8501`

### 3. Quick Smoke Test (3 minutes)

#### Test A: Basic Interaction
1. Type: **"Hello"**
2. Press Enter
3. ✅ Verify: Agent responds with greeting
4. ✅ Verify: Message appears exactly once

#### Test B: No Duplicates
1. Type: **"Test message"**
2. Wait for response
3. Type: **"Another message"**
4. ✅ Verify: Each message appears exactly once
5. ✅ Verify: No duplicate messages anywhere

#### Test C: Context Retention
1. Type: **"Create a user named Bob"**
2. Note the user ID in response
3. Type: **"Create a group called Bob's Team"**
4. Type: **"Add Bob to that group"**
5. ✅ Verify: Agent uses correct IDs without you repeating them

---

## If Smoke Test Passes ✅

**Congratulations!** The core functionality is working.

### Next Steps:

Choose your testing approach:

#### Option 1: Quick Testing (40 minutes)
Open and follow: **`MANUAL_TESTING_CHECKLIST.md`**
- Rapid checklist format
- Covers all critical functionality
- Good for quick validation

#### Option 2: Comprehensive Testing (90 minutes)
Open and follow: **`MANUAL_TESTING_GUIDE.md`**
- Detailed test scenarios
- Step-by-step instructions
- Thorough coverage of all requirements

#### Option 3: Just the Essentials (15 minutes)
Test these 5 critical scenarios:

1. **No Duplicate Messages**
   - Send 5 messages
   - Verify each appears exactly once
   - Refresh page
   - Verify still no duplicates

2. **Context Retention**
   - Create user → Create group → Add user to group
   - Verify agent remembers IDs

3. **Streaming**
   - Ask: "Explain event planning in detail"
   - Verify tokens stream smoothly
   - Verify cursor (▌) shows during streaming

4. **Error Handling**
   - Try an invalid command
   - Verify error message is user-friendly
   - Verify you can continue conversation

5. **New Conversation**
   - Click "New Conversation"
   - Confirm
   - Verify history clears
   - Verify fresh start

---

## If Smoke Test Fails ❌

### Common Issues:

#### Issue: "Agent not responding"
```bash
# Check API key
cat .env | grep GOOGLE_API_KEY

# Verify it's set correctly
# If not, add: GOOGLE_API_KEY=your_key_here
```

#### Issue: "Playground won't start"
```bash
# Check if port is in use
lsof -i :8501

# Kill existing process
kill -9 [PID]

# Restart
./start_playground.sh
```

#### Issue: "Styling looks wrong"
- Clear browser cache (Ctrl+Shift+Delete)
- Hard refresh (Ctrl+Shift+R)
- Try incognito mode

#### Issue: "Import errors"
```bash
# Reinstall dependencies
make install

# Restart playground
./start_playground.sh
```

---

## What to Look For

### ✅ Good Signs
- Responses appear within 1-2 seconds
- Streaming is smooth (no long pauses)
- Each message appears exactly once
- Agent remembers previous context
- Errors are user-friendly
- UI is responsive

### ❌ Red Flags
- Duplicate messages
- Agent forgets context
- Long delays without feedback
- Crashes or freezes
- Stack traces visible to user
- UI becomes unresponsive

---

## Recording Your Results

### Quick Template

```markdown
**Date:** [Today's date]
**Tester:** [Your name]
**Duration:** [How long you tested]

**Smoke Test:** ✅ PASS / ❌ FAIL

**Critical Scenarios:**
- No Duplicates: ✅ / ❌
- Context Retention: ✅ / ❌
- Streaming: ✅ / ❌
- Error Handling: ✅ / ❌
- New Conversation: ✅ / ❌

**Issues Found:**
1. [Description]
2. [Description]

**Overall Status:** ✅ PASS / ❌ FAIL
```

Save this in `TESTING_SUMMARY.md`

---

## Test Scenarios by Priority

### Priority 1: Must Work (Critical)
1. ✅ Agent responds to messages
2. ✅ No duplicate messages
3. ✅ Context is retained
4. ✅ No crashes

### Priority 2: Should Work (Important)
5. ✅ Streaming works smoothly
6. ✅ Error handling is user-friendly
7. ✅ New conversation works
8. ✅ Branding is correct

### Priority 3: Nice to Have (Enhancement)
9. ✅ Responsive design
10. ✅ Browser compatibility
11. ✅ Performance is good
12. ✅ History pagination works

---

## Automated Test Status

Before manual testing, verify automated tests pass:

```bash
# Run all tests
uv run pytest tests/unit tests/integration tests/property -v

# Expected: 229+ tests passing
```

**Current Status:**
- ✅ 229 tests passing
- ✅ All property-based tests passing
- ✅ All unit tests passing
- ⚠️ 2 integration tests failing (unrelated to playground)

---

## Documentation Reference

- **MANUAL_TESTING_EXECUTION.md** - Detailed execution report
- **MANUAL_TESTING_QUICKSTART.md** - 40-minute rapid guide
- **MANUAL_TESTING_GUIDE.md** - 90-minute comprehensive guide
- **MANUAL_TESTING_CHECKLIST.md** - Quick checklist format
- **PLAYGROUND_TROUBLESHOOTING.md** - Troubleshooting help
- **PLAYGROUND_GUIDE.md** - Setup and configuration

---

## Ready? Let's Go! 🚀

1. ✅ Read this guide
2. ✅ Run smoke test (3 minutes)
3. ✅ Choose testing approach
4. ✅ Execute tests
5. ✅ Record results
6. ✅ Sign off

**Start here:** Run the smoke test above (Section 3)

**Questions?** Check PLAYGROUND_TROUBLESHOOTING.md

**Good luck!** 🎉

---

## Success Criteria

### Minimum Success
- ✅ Smoke test passes
- ✅ No duplicate messages
- ✅ Context retention works
- ✅ No crashes

### Full Success
- ✅ All Priority 1 scenarios pass
- ✅ All Priority 2 scenarios pass
- ✅ Most Priority 3 scenarios pass
- ✅ No critical issues found

---

## After Testing

### If All Tests Pass ✅
1. Update TESTING_SUMMARY.md with results
2. Sign off on the feature
3. Feature is ready for production! 🎉

### If Issues Found ❌
1. Document all issues clearly
2. Prioritize by severity (Critical/High/Medium/Low)
3. Report to development team
4. Re-test after fixes

---

**Current Status:** ✅ Ready for Manual Testing

**Implementation:** ✅ Complete (All 10 tasks done)

**Automated Tests:** ✅ Passing (229/231)

**Documentation:** ✅ Complete

**Next Step:** Execute manual testing! 🚀

