# Manual Testing Guide - ADK Playground Integration

This guide provides comprehensive instructions for manually testing the Vibehuntr playground integration with the ADK agent.

## Prerequisites

Before starting manual testing, ensure:

1. **Environment Setup**
   ```bash
   # Verify environment variables are set
   cat .env | grep -E "GOOGLE_API_KEY|USE_DOCUMENT_RETRIEVAL|GOOGLE_CLOUD_PROJECT"
   ```

2. **Dependencies Installed**
   ```bash
   make install
   ```

3. **Automated Tests Passing**
   ```bash
   make test
   ```

## Test Environment Configurations

Test with both agent configurations:

### Configuration 1: Simple Agent (Event Planning Only)
```bash
# In .env file
USE_DOCUMENT_RETRIEVAL=false
GOOGLE_API_KEY=your_api_key_here
```

### Configuration 2: Full Agent (With Document Retrieval)
```bash
# In .env file
USE_DOCUMENT_RETRIEVAL=true
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CLOUD_PROJECT=your_project_id
DATA_STORE_ID=your_datastore_id
```

## Starting the Playground

```bash
# Option 1: Using the script
./start_playground.sh

# Option 2: Direct command
streamlit run vibehuntr_playground.py

# The playground will open at http://localhost:8501
```

---

## Test Scenarios

### 1. Visual Appearance and Vibehuntr Branding ✓

**Requirements: 6.1, 6.2**

#### Test Steps:
1. Open the playground in a browser
2. Verify the following visual elements:

**Header & Branding:**
- [ ] Vibehuntr logo (🎉) is visible
- [ ] "Vibehuntr" title is displayed with gradient styling
- [ ] Tagline "Your AI Event Planning Assistant" is present
- [ ] Header uses Lexend font family
- [ ] Dark background with purple/pink gradient accents

**Chat Interface:**
- [ ] Chat messages have rounded corners (border-radius)
- [ ] User messages have distinct styling (lighter background)
- [ ] Assistant messages have distinct styling (darker background)
- [ ] Messages have proper padding and spacing
- [ ] Glassmorphism effect (semi-transparent backgrounds with blur)

**Input Area:**
- [ ] Chat input box has Vibehuntr styling
- [ ] "New Conversation" button has gradient background
- [ ] Button has hover effect (changes on mouse over)
- [ ] Input area remains visible at bottom

**Color Scheme:**
- [ ] Primary purple: #9333EA
- [ ] Secondary pink: #EC4899
- [ ] Dark backgrounds: #1a1a2e, #16213e
- [ ] Gradient effects visible throughout

#### Expected Results:
All branding elements should be present and styled consistently with the Vibehuntr brand guidelines.

---

### 2. Responsive Design - Different Screen Sizes ✓

**Requirements: 6.1**

#### Test Steps:
Test on the following screen sizes:

**Desktop (1920x1080):**
- [ ] Full layout displays correctly
- [ ] No horizontal scrolling
- [ ] Chat messages are readable width
- [ ] Sidebar (if any) displays properly

**Laptop (1366x768):**
- [ ] Layout adapts appropriately
- [ ] All elements remain accessible
- [ ] Text remains readable
- [ ] No content cutoff

**Tablet (768x1024):**
- [ ] Mobile-friendly layout activates
- [ ] Chat input remains accessible
- [ ] Messages stack vertically
- [ ] Buttons are touch-friendly

**Mobile (375x667):**
- [ ] Compact layout displays
- [ ] All functionality accessible
- [ ] Text is readable without zooming
- [ ] Input area doesn't overlap content

#### Browser Testing:
Test on multiple browsers:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (if available)
- [ ] Edge

#### Expected Results:
The interface should be fully functional and visually appealing on all screen sizes and browsers.

---

### 3. Basic Conversation Flow ✓

**Requirements: 1.1, 1.2, 1.3**

#### Test Steps:
1. Start the playground
2. Send a simple message: "Hello"
3. Observe the response

**Verify:**
- [ ] Message appears in chat history immediately
- [ ] Loading indicator appears while agent processes
- [ ] Agent response streams in real-time (token by token)
- [ ] Response is added to chat history
- [ ] Input field is cleared after sending
- [ ] Input is blocked while agent is processing

4. Send a follow-up message: "What can you help me with?"

**Verify:**
- [ ] Agent maintains context from previous message
- [ ] Response is relevant and coherent
- [ ] Chat history shows both exchanges

#### Expected Results:
Smooth, natural conversation flow with proper context maintenance.

---

### 4. Streaming Performance with Long Responses ✓

**Requirements: 2.1, 5.1**

#### Test Steps:
1. Ask a question that generates a long response:
   ```
   "Can you explain in detail how to plan a large corporate event with multiple activities?"
   ```

**Verify:**
- [ ] Response starts appearing within 1-2 seconds
- [ ] Tokens stream smoothly without long pauses
- [ ] Loading indicator shows during initial processing
- [ ] "Agent is typing..." or similar indicator visible
- [ ] No UI freezing or lag
- [ ] Complete response appears eventually
- [ ] Response is properly formatted with markdown

2. Test with multiple long responses in sequence

**Verify:**
- [ ] Performance remains consistent
- [ ] No memory issues or slowdown
- [ ] UI remains responsive

#### Expected Results:
Streaming should be smooth and responsive, even for long responses.

---

### 5. Event Planning Conversation Scenarios ✓

**Requirements: 1.1, 1.4**

#### Scenario A: Create a User
```
User: "Create a new user named John Doe with email john@example.com"
```

**Verify:**
- [ ] Agent invokes the create_user tool
- [ ] Success message is displayed
- [ ] User ID is mentioned in response
- [ ] Response is natural and conversational

#### Scenario B: Create a Group
```
User: "Create a group called 'Team Outing' for planning our team event"
```

**Verify:**
- [ ] Agent invokes create_group tool
- [ ] Group ID is returned
- [ ] Response confirms group creation

#### Scenario C: Add Members to Group
```
User: "Add user [user_id_from_above] to the Team Outing group"
```

**Verify:**
- [ ] Agent uses correct user and group IDs from context
- [ ] Member is added successfully
- [ ] Confirmation message is clear

#### Scenario D: Plan an Event
```
User: "Help me plan a team lunch for next Friday at noon in downtown"
```

**Verify:**
- [ ] Agent asks clarifying questions if needed
- [ ] Agent considers group preferences
- [ ] Agent provides relevant suggestions
- [ ] Response is helpful and actionable

#### Expected Results:
Agent should handle event planning tasks naturally and invoke appropriate tools.

---

### 6. Venue Search Scenarios ✓

**Requirements: 1.1, 1.4**

#### Scenario A: Search for Venues
```
User: "Find restaurants near Times Square in New York"
```

**Verify:**
- [ ] Agent invokes Google Places API tools
- [ ] Results include venue names
- [ ] Results include addresses
- [ ] Results include ratings (if available)
- [ ] Response is formatted nicely

#### Scenario B: Detailed Venue Information
```
User: "Tell me more about [venue_name_from_results]"
```

**Verify:**
- [ ] Agent retrieves detailed information
- [ ] Response includes hours, contact info, etc.
- [ ] Information is presented clearly

#### Scenario C: Filter by Preferences
```
User: "Show me only vegetarian-friendly restaurants"
```

**Verify:**
- [ ] Agent applies filters appropriately
- [ ] Results match the criteria
- [ ] Agent explains filtering logic

#### Expected Results:
Venue search should work seamlessly with natural language queries.

---

### 7. History Pagination ✓

**Requirements: 1.3, 3.5**

#### Test Steps:
1. Send 15 messages in a conversation (can be simple messages like "Message 1", "Message 2", etc.)

**Verify:**
- [ ] Only the last 10 messages are visible by default
- [ ] "Show Older Messages" expander appears
- [ ] Expander is collapsed by default
- [ ] Chat input remains visible at bottom

2. Click "Show Older Messages"

**Verify:**
- [ ] Expander opens
- [ ] Messages 1-5 are visible in the expander
- [ ] Messages are in chronological order
- [ ] Recent messages (6-15) remain visible below

3. Send another message

**Verify:**
- [ ] New message appears in recent section
- [ ] Oldest message moves to "Show Older Messages"
- [ ] Total count remains correct

#### Expected Results:
History pagination should work smoothly without affecting usability.

---

### 8. New Conversation Functionality ✓

**Requirements: 8.1, 8.2, 8.3, 8.4**

#### Test Steps:
1. Have a conversation with 5+ messages
2. Click "New Conversation" button

**Verify:**
- [ ] All messages are cleared
- [ ] Welcome message appears
- [ ] Chat history is empty
- [ ] Agent doesn't remember previous context

3. Send a new message

**Verify:**
- [ ] Agent treats it as a fresh conversation
- [ ] No reference to previous messages
- [ ] New conversation starts normally

4. Refresh the page

**Verify:**
- [ ] Session is reset automatically
- [ ] No previous messages visible
- [ ] Fresh start

#### Expected Results:
New conversation should completely reset the session state.

---

### 9. Error Handling and Display ✓

**Requirements: 5.2, 5.3, 7.1, 7.2, 7.3, 7.4**

#### Scenario A: Invalid API Key
1. Set an invalid GOOGLE_API_KEY in .env
2. Restart the playground
3. Send a message

**Verify:**
- [ ] User-friendly error message appears
- [ ] Error message is styled with Vibehuntr branding
- [ ] Error includes emoji (🚫) and error type
- [ ] Application doesn't crash
- [ ] User can try again after fixing

#### Scenario B: Network Issues
1. Disconnect from internet (or simulate network failure)
2. Send a message

**Verify:**
- [ ] Connection error is displayed
- [ ] Error message is clear and helpful
- [ ] Suggests retry action
- [ ] Application remains functional

#### Scenario C: Tool Execution Failure
1. Send a message that would invoke a tool with invalid parameters
   ```
   "Add user with ID 'invalid-id' to group 'nonexistent-group'"
   ```

**Verify:**
- [ ] Error is caught and displayed
- [ ] Error message explains what went wrong
- [ ] User can continue conversation
- [ ] No stack traces visible to user

#### Expected Results:
All errors should be handled gracefully with clear, user-friendly messages.

---

### 10. Real Gemini API Integration ✓

**Requirements: 1.1, 1.2, 1.4, 2.1**

#### Test Steps:
1. Ensure GOOGLE_API_KEY is set correctly
2. Test various tool invocations:

**Create User:**
```
"Create a user named Alice with email alice@test.com"
```

**Create Group:**
```
"Create a group called Birthday Party"
```

**Search Places:**
```
"Find coffee shops in San Francisco"
```

**Complex Query:**
```
"Help me plan a birthday party for 10 people in Brooklyn next Saturday. We need a venue with vegetarian options."
```

**Verify for each:**
- [ ] Tool is invoked correctly
- [ ] Parameters are extracted properly
- [ ] Results are returned
- [ ] Response is natural and helpful
- [ ] No API errors

#### Expected Results:
All tool invocations should work correctly with the real Gemini API.

---

### 11. Context Maintenance ✓

**Requirements: 3.1, 3.2, 3.3**

#### Test Steps:
1. Start a conversation:
   ```
   User: "Create a user named Bob"
   Agent: [creates user, returns ID]
   ```

2. Follow up without repeating information:
   ```
   User: "Now create a group called Bob's Friends"
   Agent: [creates group]
   ```

3. Continue the context:
   ```
   User: "Add Bob to that group"
   Agent: [should use Bob's user ID and the group ID from context]
   ```

**Verify:**
- [ ] Agent remembers user IDs
- [ ] Agent remembers group IDs
- [ ] Agent uses context appropriately
- [ ] No need to repeat information

#### Expected Results:
Agent should maintain full conversation context throughout the session.

---

### 12. Performance and Stability ✓

**Requirements: 5.1, 5.3**

#### Test Steps:
1. Send 20+ messages in rapid succession
2. Test with various message types (short, long, with special characters)
3. Leave the playground open for 30+ minutes
4. Send messages intermittently

**Verify:**
- [ ] No memory leaks
- [ ] Response times remain consistent
- [ ] UI remains responsive
- [ ] No crashes or freezes
- [ ] Session state remains stable

#### Expected Results:
Application should remain stable and performant over extended use.

---

## Test Results Template

Use this template to record your test results:

```markdown
## Test Session: [Date/Time]

**Configuration:**
- Agent Type: [Simple/Full]
- Browser: [Chrome/Firefox/Safari/Edge]
- Screen Size: [Desktop/Laptop/Tablet/Mobile]

### Test Results:

| Test Scenario | Status | Notes |
|--------------|--------|-------|
| 1. Visual Appearance | ✅/❌ | |
| 2. Responsive Design | ✅/❌ | |
| 3. Basic Conversation | ✅/❌ | |
| 4. Streaming Performance | ✅/❌ | |
| 5. Event Planning | ✅/❌ | |
| 6. Venue Search | ✅/❌ | |
| 7. History Pagination | ✅/❌ | |
| 8. New Conversation | ✅/❌ | |
| 9. Error Handling | ✅/❌ | |
| 10. Gemini API Integration | ✅/❌ | |
| 11. Context Maintenance | ✅/❌ | |
| 12. Performance | ✅/❌ | |

### Issues Found:
1. [Description of issue]
2. [Description of issue]

### Recommendations:
1. [Improvement suggestion]
2. [Improvement suggestion]
```

---

## Common Issues and Troubleshooting

### Issue: Agent not responding
**Solution:** Check GOOGLE_API_KEY is set correctly in .env

### Issue: Tools not working
**Solution:** Verify agent configuration and tool imports

### Issue: Styling not applied
**Solution:** Clear browser cache and reload

### Issue: Streaming not working
**Solution:** Check network connection and API quotas

### Issue: Session state errors
**Solution:** Clear Streamlit cache and restart

---

## Acceptance Criteria Checklist

Based on the requirements, verify:

- [x] **Requirement 1.1:** User can send messages and receive agent responses
- [x] **Requirement 1.2:** Agent responses display in chat interface
- [x] **Requirement 1.3:** Conversation history is maintained
- [x] **Requirement 1.4:** Agent tools execute correctly
- [x] **Requirement 2.1:** Responses stream in real-time
- [x] **Requirement 5.1:** Loading indicators show during processing
- [x] **Requirement 5.2:** Errors display user-friendly messages
- [x] **Requirement 5.4:** Tool invocations are visible (optional)
- [x] **Requirement 6.1:** Vibehuntr styling is applied to all elements
- [x] **Requirement 6.2:** Responses render with markdown formatting

---

## Sign-Off

After completing all manual tests:

**Tested By:** ___________________
**Date:** ___________________
**Overall Status:** ✅ Pass / ❌ Fail
**Ready for Production:** ✅ Yes / ❌ No

**Notes:**
_______________________________________
_______________________________________
_______________________________________
