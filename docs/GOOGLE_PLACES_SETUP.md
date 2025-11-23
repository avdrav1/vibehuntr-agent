# Google Places API Integration - Setup Guide

## 🎯 What This Adds

Your event planning agent can now:
- **Search real venues**: Find restaurants, parks, museums, etc.
- **Get reviews & ratings**: See what others think
- **Check prices**: Filter by budget
- **View details**: Hours, phone, website, photos
- **Make better recommendations**: Real-world data!

## 🚀 Quick Setup

### Step 1: Get a Google Places API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project (or select existing)
3. Enable **Places API** and **Geocoding API**
4. Create credentials → API Key
5. Copy your API key

### Step 2: Add to .env File

Add this line to your `.env` file:

```bash
GOOGLE_API_KEY=your-gemini-key-here
GOOGLE_PLACES_API_KEY=your-places-key-here
```

### Step 3: Test It!

```bash
uv run python app/event_planning/chat_interface.py
```

Then try:
```
Find Italian restaurants in San Francisco
Show me hiking trails near Seattle
What are good museums in New York?
```

## 💬 Example Conversations

### Finding Restaurants

```
You: Find Italian restaurants in San Francisco with good ratings

Agent: Found 5 venue(s) for 'Italian restaurants':

1. **Tony's Pizza Napoletana**
   📍 1570 Stockton St, San Francisco, CA
   ⭐⭐⭐⭐⭐ 4.5/5 (2,847 reviews)
   💰 Price: $$
   🆔 Place ID: ChIJ...

2. **Flour + Water**
   📍 2401 Harrison St, San Francisco, CA
   ⭐⭐⭐⭐⭐ 4.6/5 (1,523 reviews)
   💰 Price: $$$
   🆔 Place ID: ChIJ...

Would you like details about any of these?
```

### Getting Details

```
You: Tell me more about Tony's Pizza

Agent: **Tony's Pizza Napoletana**

📍 Address: 1570 Stockton St, San Francisco, CA
📞 Phone: (415) 835-9888
🌐 Website: tonyspizzanapoletana.com

⭐⭐⭐⭐⭐ 4.5/5 (2,847 reviews)
💰 Price Level: $$

⏰ Hours: Open now ✅

📝 Recent Reviews:

1. ⭐⭐⭐⭐⭐ - Sarah M.
   "Best pizza in SF! The margherita is incredible..."

2. ⭐⭐⭐⭐ - John D.
   "Great atmosphere and authentic Italian pizza..."
```

### Planning with Real Venues

```
You: Plan a dinner event at Tony's Pizza for my Weekend Warriors group

Agent: Great choice! Let me create that event for you.

✓ Created event 'Dinner at Tony's Pizza'!
  Activity: dining
  When: 2025-01-25 19:00 to 21:00
  Where: Tony's Pizza Napoletana (1570 Stockton St)
  Participants: 5 members
  Status: pending
  Budget: $30 per person

The restaurant has a 4.5/5 rating with great reviews! 
Should I finalize this event?
```

## 🛠️ Advanced Features

### Budget Filtering

```
Find restaurants under $20 per person in downtown
```

The agent will filter by price level automatically.

### Rating Requirements

```
Show me highly-rated (4+ stars) coffee shops nearby
```

### Activity-Specific Search

```
Find family-friendly activities in the area
Show me outdoor venues for a group event
```

## 🔧 API Configuration

### Enable Required APIs

In Google Cloud Console, enable:
1. **Places API** (New) - For place search and details
2. **Geocoding API** - For location lookups
3. **Maps JavaScript API** (optional) - For displaying maps

### Set Usage Limits (Optional)

To avoid unexpected charges:
1. Go to APIs & Services → Quotas
2. Set daily limits for Places API
3. Enable billing alerts

### Pricing

- **Places API**: $17 per 1,000 requests (Text Search)
- **Place Details**: $17 per 1,000 requests
- **Free tier**: $200/month credit

Most personal use stays within free tier!

## 🎨 RAG Enhancement (Future)

Want to build a full RAG system? Here's the plan:

### Phase 1: Vector Database (Current)
Store venue data in Vertex AI Vector Search for semantic search.

### Phase 2: Personalization
Learn from user feedback to improve recommendations.

### Phase 3: Context-Aware
Consider group preferences, past events, and feedback.

See `GOOGLE_PLACES_RAG_DESIGN.md` for full architecture!

## 🐛 Troubleshooting

### "Google Places API not configured"

**Solution:** Add `GOOGLE_PLACES_API_KEY` to your `.env` file.

### "API key not valid"

**Check:**
1. API key is correct (no extra spaces)
2. Places API is enabled in Google Cloud Console
3. API key has no restrictions blocking your IP

### "No venues found"

**Try:**
- Be more specific: "Italian restaurants" not just "food"
- Add a location: "in San Francisco"
- Check your search radius

### "Quota exceeded"

You've hit the API limit. Either:
- Wait for quota to reset (daily)
- Increase quota in Google Cloud Console
- Implement caching (see RAG design)

## 📊 Monitoring Usage

Check your API usage:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. APIs & Services → Dashboard
3. View Places API metrics

## 🎉 What's Next?

Now that you have real venue data, you can:

1. **Build a RAG system** - Cache popular venues
2. **Add photos** - Show venue images
3. **Integrate maps** - Display locations visually
4. **Learn preferences** - Personalize recommendations
5. **Compare venues** - Side-by-side analysis

See `GOOGLE_PLACES_RAG_DESIGN.md` for the full roadmap!

Happy venue hunting! 🎊
