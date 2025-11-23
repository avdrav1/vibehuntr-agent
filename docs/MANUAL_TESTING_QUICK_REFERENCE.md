# 🎯 Manual Testing Quick Reference Card

**Print this or keep it open while testing!**

---

## 🚀 Start Testing (30 seconds)

```bash
./start_playground.sh
```

Opens at: `http://localhost:8501`

---

## ✅ 5 Critical Tests (15 minutes)

### 1. No Duplicates (3 min)
```
Send: "Test 1"
Send: "Test 2"
Send: "Test 3"
✓ Each message appears exactly once
✓ Refresh page → still no duplicates
```

### 2. Context Works (3 min)
```
Send: "Create a user named Alice"
Send: "Create a group called Alice's Friends"
Send: "Add Alice to that group"
✓ Agent uses correct IDs without repeating
```

### 3. Streaming Works (3 min)
```
Send: "Explain event planning in detail"
✓ Tokens appear progressively
✓ Cursor (▌) shows during streaming
✓ Cursor disappears when done
```

### 4. Errors are Friendly (3 min)
```
Send: "Add user invalid-id to group bad-group"
✓ Error message is clear
✓ No stack traces visible
✓ Can continue conversation
```

### 5. New Conversation (3 min)
```
Have 5+ message conversation
Click "New Conversation" → Confirm
✓ History clears
✓ Welcome message shows
✓ Agent forgets previous context
```

---

## 🎨 Visual Checklist (2 minutes)

- [ ] 🎉 Vibehuntr logo visible
- [ ] 🌈 Purple/pink gradient colors
- [ ] 🌙 Dark theme applied
- [ ] 💬 Messages styled correctly
- [ ] 🔘 Buttons have gradient backgrounds
- [ ] 📝 Input area at bottom

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| Agent not responding | Check `GOOGLE_API_KEY` in `.env` |
| Port already in use | `lsof -i :8501` then `kill -9 [PID]` |
| Styling broken | Clear cache (Ctrl+Shift+Delete) |
| Import errors | Run `make install` |

---

## 📊 Pass/Fail Criteria

### ✅ PASS if:
- All 5 critical tests pass
- No duplicate messages
- Context retention works
- No crashes

### ❌ FAIL if:
- Duplicate messages appear
- Context is lost
- Frequent crashes
- Agent doesn't respond

---

## 📝 Quick Results Template

```
Date: ___________
Tester: ___________

Critical Tests:
1. No Duplicates: ✅ / ❌
2. Context Works: ✅ / ❌
3. Streaming Works: ✅ / ❌
4. Errors Friendly: ✅ / ❌
5. New Conversation: ✅ / ❌

Visual Check: ✅ / ❌

Overall: ✅ PASS / ❌ FAIL

Issues:
_________________________
_________________________
```

---

## 🔗 Full Documentation

- **Quick Start:** `START_MANUAL_TESTING.md`
- **40-min Test:** `MANUAL_TESTING_CHECKLIST.md`
- **90-min Test:** `MANUAL_TESTING_GUIDE.md`
- **Troubleshooting:** `PLAYGROUND_TROUBLESHOOTING.md`

---

## 🎯 Success = All 5 Tests Pass ✅

**Time Required:** 15 minutes
**Difficulty:** Easy
**Prerequisites:** API key configured

---

**Ready? Start with Test 1! 🚀**

