# Demo Conversation - Event Planning Agent

This is a sample conversation showing the agent's capabilities.

---

**You:** Hi! I want to start planning events with my friends.

**Agent:** Hello! I'd be happy to help you plan events with your friends! 🎉

To get started, I can help you:
- Create user profiles for you and your friends
- Set up friend groups
- Find optimal meeting times
- Plan and organize events
- Collect feedback after events

What would you like to do first? Would you like to create a user profile?

---

**You:** Yes, create a user for me. My name is Sarah and my email is sarah@example.com

**Agent:** ✓ Created user profile for Sarah (sarah@example.com). They can now join groups and plan events!

Would you like to set your preferences (favorite activities, budget, dietary restrictions) or add your availability?

---

**You:** I like hiking and dining out. My budget is around $50 per event.

**Agent:** ✓ Updated preferences for Sarah:
  Activities: hiking (0.8), dining (0.7)
  Max Budget: $50

Great! Now you're all set up. Would you like to:
1. Create a friend group
2. Add your availability
3. Invite friends to join

---

**You:** Let me add my availability first. I'm free this Saturday from 10am to 4pm.

**Agent:** ✓ Added availability for Sarah: 2025-01-25 10:00 to 2025-01-25 16:00 (UTC)

Perfect! Now when you create events, I'll make sure they fit your schedule. Would you like to create a friend group next?

---

**You:** Yes, create a group called "Adventure Squad" with me as the creator.

**Agent:** ✓ Created group 'Adventure Squad' with 1 member(s)!

Your group is ready! You can now:
- Add more members to the group
- Find optimal meeting times
- Plan events together

Would you like to add more friends to the group?

---

**You:** Let me create another user first - my friend Mike with email mike@example.com

**Agent:** ✓ Created user profile for Mike (mike@example.com). They can now join groups and plan events!

Great! Mike is now in the system. Would you like to add Mike to your Adventure Squad group?

---

**You:** Yes, add Mike to Adventure Squad

**Agent:** I'll add Mike to the Adventure Squad group for you.

✓ Added Mike to Adventure Squad! The group now has 2 members.

Your Adventure Squad is growing! What would you like to do next?

---

**You:** When can our group meet for a 3-hour event?

**Agent:** Let me check the availability for your Adventure Squad group...

Found 1 optimal time slot(s) for Adventure Squad:

1. 2025-01-25 10:00 to 13:00
   50% attendance (1 members)

Note: Only Sarah has provided availability. Mike should add their availability for better scheduling! Would you like me to help you plan an event for this time slot?

---

**You:** Yes, let's plan a hiking event called "Mountain Adventure" for Saturday at 10am

**Agent:** ✓ Created event 'Mountain Adventure'!
  Activity: hiking
  When: 2025-01-25 10:00 to 13:00
  Where: Mountain Trail
  Participants: 2 members
  Status: pending
  Budget: $50.0 per person

Your event is created! It's currently in PENDING status. When you're ready to confirm it, just say "finalize the Mountain Adventure event" and I'll make it official! 🎉

---

**You:** Finalize the Mountain Adventure event

**Agent:** ✓ Event 'Mountain Adventure' is now confirmed! 🎉

Congratulations! Your hiking trip is all set for Saturday at 10am. Your Adventure Squad is ready to go!

After the event, you can submit feedback to help me suggest even better events in the future. Have a great time! 🏔️

---

**You:** Show me all our events

**Agent:** All events:

• Mountain Adventure (confirmed)
  hiking at Mountain Trail
  2025-01-25 10:00

You have 1 confirmed event! Looking forward to hearing how it goes! 🎉

---

**You:** Thanks! This is really helpful.

**Agent:** You're very welcome! I'm glad I could help you plan your event! 😊

Feel free to come back anytime to:
- Plan more events
- Add more friends to your groups
- Update your preferences
- Submit feedback after events

Have an amazing time on your Mountain Adventure! 🏔️✨

---

## Key Takeaways from This Demo

1. **Natural Conversation**: The agent maintains context and flows naturally
2. **Proactive Suggestions**: Offers next steps without being asked
3. **Friendly Tone**: Uses emojis and encouraging language
4. **Smart Linking**: Automatically connects related actions (create user → add to group)
5. **Clear Status**: Always confirms actions with ✓ and explains what happened
6. **Helpful Guidance**: Points out when information is missing (Mike's availability)
7. **Celebration**: Celebrates successes with 🎉 and positive language

## Try It Yourself!

Start the chat interface:
```bash
uv run python app/event_planning/chat_interface.py
```

Then try variations of these commands to see how the agent adapts!
