# Quick Start Guide

## Interactive Menu (Easy Mode!)

Run the interactive menu:

```bash
uv run python cli/interactive_menu.py
```

### Example Workflow

1. **Create Users**
   - Choose option `1` (User Management)
   - Choose option `1` (Create User)
   - Enter name and email
   - Repeat for multiple users

2. **Add Preferences & Availability**
   - Choose option `1` (User Management)
   - Choose option `4` (Update Preferences)
   - Select user by **name or number** (no ID needed!)
   - Enter preferences
   - Then choose option `5` (Add Availability)
   - Select user by name
   - Enter availability times

3. **Create a Group**
   - Choose option `2` (Group Management)
   - Choose option `1` (Create Group)
   - Enter group name
   - Select creator by **name** (no ID!)
   - Select additional members by **name** (comma-separated)

4. **Create an Event**
   - Choose option `3` (Event Management)
   - Choose option `1` (Create Event)
   - Select group by **name**
   - Enter event details
   - Event is created in PENDING status

5. **Finalize the Event**
   - Choose option `3` (Event Management)
   - Choose option `2` (Finalize Event)
   - Select event by **name**
   - Event is now CONFIRMED!

6. **Submit Feedback**
   - Choose option `4` (Feedback)
   - Choose option `1` (Submit Feedback)
   - Select event by **name**
   - Select user by **name**
   - Enter rating and comments

## Key Features

✅ **No IDs Required** - Select everything by name or number
✅ **Interactive Menus** - Easy navigation
✅ **Multi-Select** - Add multiple members at once
✅ **Validation** - Helpful error messages
✅ **View Details** - See full information about users, groups, and events

## Tips

- You can type names or numbers when selecting items
- Type `cancel` to go back
- Type `done` when finished selecting multiple items
- Names are case-insensitive
- Use commas to select multiple items at once (e.g., "1,3,5" or "Alice,Bob")

## Example Session

```
=== Event Planning Agent ===
1. User Management
2. Group Management
3. Event Management
4. Feedback
5. View Information
6. Exit

Choose an option: 1

--- User Management ---
1. Create User
2. List Users
3. View User Details
4. Update Preferences
5. Add Availability
6. Back

Choose an option: 1

--- Create User ---
Name: Alice
Email: alice@example.com

✓ User created successfully!
  Name: Alice
  Email: alice@example.com
```

Much easier than remembering UUIDs!
