# Quick Manual Testing Checklist

Use this checklist for rapid manual testing of the Vibehuntr playground.

## Pre-Testing Setup

- [ ] Environment variables configured in `.env`
- [ ] Dependencies installed (`make install`)
- [ ] Automated tests passing (`make test`)
- [ ] Playground started (`./start_playground.sh`)

---

## Quick Visual Check (2 minutes)

- [ ] Vibehuntr logo and branding visible
- [ ] Dark theme with purple/pink gradients
- [ ] Chat interface styled correctly
- [ ] Buttons have gradient backgrounds
- [ ] Input area at bottom

---

## Basic Functionality (5 minutes)

- [ ] Send "Hello" - receives response
- [ ] Response streams token-by-token
- [ ] Loading indicator shows while processing
- [ ] Message history displays correctly
- [ ] Input blocked during processing

---

## Tool Invocation (5 minutes)

- [ ] Create user: "Create a user named Test User"
- [ ] Create group: "Create a group called Test Group"
- [ ] Search places: "Find restaurants in New York"
- [ ] All tools execute successfully

---

## History & Navigation (3 minutes)

- [ ] Send 15 messages
- [ ] Only last 10 visible by default
- [ ] "Show Older Messages" appears
- [ ] Older messages accessible in expander
- [ ] Chat input remains at bottom

---

## New Conversation (2 minutes)

- [ ] Click "New Conversation" button
- [ ] Confirmation dialog appears
- [ ] Clicking "Yes" clears history
- [ ] Welcome message displays
- [ ] Fresh conversation starts

---

## Error Handling (3 minutes)

- [ ] Test with invalid API key (if safe)
- [ ] Error message is user-friendly
- [ ] Error styled with Vibehuntr branding
- [ ] Application doesn't crash
- [ ] Can continue after error

---

## Responsive Design (5 minutes)

- [ ] Desktop (1920x1080) - full layout
- [ ] Laptop (1366x768) - adapts correctly
- [ ] Tablet (768x1024) - mobile-friendly
- [ ] Mobile (375x667) - compact layout

---

## Browser Compatibility (5 minutes)

- [ ] Chrome/Chromium - works correctly
- [ ] Firefox - works correctly
- [ ] Safari - works correctly (if available)
- [ ] Edge - works correctly (if available)

---

## Performance (5 minutes)

- [ ] Long response streams smoothly
- [ ] Multiple messages in sequence
- [ ] No lag or freezing
- [ ] Memory usage stable
- [ ] UI remains responsive

---

## Context Maintenance (3 minutes)

- [ ] Create user, remember ID
- [ ] Create group, remember ID
- [ ] Reference previous entities
- [ ] Agent uses context correctly

---

## Total Time: ~40 minutes

## Pass Criteria

✅ **PASS** if:
- All critical functionality works
- No crashes or major errors
- Branding is consistent
- Performance is acceptable

❌ **FAIL** if:
- Agent doesn't respond
- Frequent crashes
- Major styling issues
- Tools don't work

---

## Quick Issue Report

**Date:** _______________
**Tester:** _______________
**Status:** ✅ PASS / ❌ FAIL

**Issues Found:**
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

**Critical Issues:** _______________________________________________

**Recommendations:** _______________________________________________
