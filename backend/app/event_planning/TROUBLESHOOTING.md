# Troubleshooting the Conversational AI Interface

## Issue: "Missing key inputs argument" or "PermissionDenied: 403"

The conversational AI agent requires Google Cloud credentials to work because it uses Gemini 2.0 Flash.

### Solution 1: Set up Google Cloud Authentication (Recommended)

1. **Install Google Cloud SDK:**
   ```bash
   # Follow instructions at: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate:**
   ```bash
   gcloud auth application-default login
   ```

3. **Set your project:**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

4. **Enable required APIs:**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

5. **Try again:**
   ```bash
   uv run python app/event_planning/chat_interface.py
   ```

### Solution 2: Use Gemini API Key (Simpler for testing)

1. **Get an API key:**
   - Go to https://aistudio.google.com/app/apikey
   - Create an API key

2. **Set the environment variable:**
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   ```

3. **Update the agent to use the API key:**
   
   Edit `app/event_planning/simple_agent.py` and change:
   ```python
   event_planning_agent = Agent(
       name="event_planning_agent",
       model="gemini-2.0-flash",
       instruction=instruction,
       tools=EVENT_PLANNING_TOOLS,
       api_key=os.getenv("GOOGLE_API_KEY"),  # Add this line
   )
   ```

4. **Try again:**
   ```bash
   uv run python app/event_planning/chat_interface.py
   ```

### Solution 3: Use the Interactive Menu Instead (No AI needed)

If you don't want to set up Google Cloud or get an API key, use the interactive menu interface instead:

```bash
uv run python cli/interactive_menu.py
```

This provides a similar experience without requiring AI or cloud credentials!

## Issue: "Default value is not supported"

This warning can be ignored - it's about optional parameters in the tool functions. The agent will still work.

## Issue: Nothing happens when I type

Make sure you:
1. Press Enter after typing your message
2. Wait a few seconds for the response (first response can take 3-5 seconds)
3. Check that you have internet connection (agent needs to call Gemini API)

## Issue: Agent doesn't understand my request

Try being more specific:
- ❌ "Do something"
- ✅ "Create a user named Alice with email alice@example.com"

## Issue: Tools fail with errors

The tools use the event planning service which stores data in the `data/` directory. Make sure:
1. The `data/` directory exists
2. You have write permissions
3. The JSON files aren't corrupted

## Still Having Issues?

1. **Check the logs** - The chat interface prints errors
2. **Test the tools directly:**
   ```bash
   uv run python app/event_planning/test_agent_tools.py
   ```
3. **Use the simpler interactive menu:**
   ```bash
   uv run python cli/interactive_menu.py
   ```

## Quick Setup Script

Here's a script to set everything up:

```bash
#!/bin/bash

# 1. Authenticate with Google Cloud
echo "Authenticating with Google Cloud..."
gcloud auth application-default login

# 2. Set project
echo "Enter your Google Cloud Project ID:"
read PROJECT_ID
gcloud config set project $PROJECT_ID

# 3. Enable APIs
echo "Enabling required APIs..."
gcloud services enable aiplatform.googleapis.com

# 4. Test the agent
echo "Testing the agent..."
uv run python app/event_planning/test_agent_tools.py

echo "Setup complete! Now try:"
echo "  uv run python app/event_planning/chat_interface.py"
```

Save this as `setup_agent.sh`, make it executable (`chmod +x setup_agent.sh`), and run it!
