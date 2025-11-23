# Google Places API + RAG Integration Design

## 🎯 Goal

Enhance the event planning agent with real-world venue data from Google Places API, including:
- Restaurant recommendations
- Activity locations (hiking trails, museums, etc.)
- Reviews and ratings
- Photos and details
- Operating hours and pricing

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│   User Query: "Find a good Italian restaurant"         │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│   Agent with Tools                                      │
│   - Event planning tools (existing)                     │
│   - search_places_tool (NEW)                           │
│   - get_place_details_tool (NEW)                       │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│   Google Places API Service                             │
│   - Text search                                         │
│   - Nearby search                                       │
│   - Place details                                       │
│   - Reviews & photos                                    │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│   RAG System (Optional Enhancement)                     │
│   - Cache popular venues in vector DB                   │
│   - Semantic search over reviews                        │
│   - Personalized recommendations                        │
└─────────────────────────────────────────────────────────┘
```

## 📋 Implementation Plan

### Phase 1: Direct Google Places Integration (Quick Win)
Add tools that call Google Places API directly.

### Phase 2: RAG Enhancement (Advanced)
Build a vector database of venues for semantic search.

### Phase 3: Personalization (Future)
Learn from user feedback to improve recommendations.


## 🚀 Phase 1: Direct Integration (IMPLEMENTED)

### What We Built

**New Files:**
- `app/event_planning/google_places_service.py` - Places API client
- `app/event_planning/places_tools.py` - Agent tools for venue search
- `GOOGLE_PLACES_SETUP.md` - Setup guide

**New Tools:**
1. `search_venues_tool` - Search for venues by query and location
2. `get_venue_details_tool` - Get detailed info including reviews

**Features:**
- ✅ Text search for any venue type
- ✅ Location-based search
- ✅ Rating and price filtering
- ✅ Reviews and ratings
- ✅ Contact info and hours
- ✅ Photo references

### Usage

```python
# The agent now understands:
"Find Italian restaurants in San Francisco"
"Show me hiking trails near Seattle"
"Get details about Tony's Pizza"
"Find budget-friendly activities"
```

## 🎯 Phase 2: RAG System (NEXT)

### Architecture

```
┌─────────────────────────────────────────┐
│   Venue Data Collection                 │
│   - Periodic API calls                  │
│   - Popular venues in target cities     │
│   - Reviews and metadata                │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│   Embedding Generation                  │
│   - Venue descriptions                  │
│   - Review summaries                    │
│   - Activity types                      │
│   - Using text-embedding-005            │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│   Vertex AI Vector Search               │
│   - Store venue embeddings              │
│   - Semantic search                     │
│   - Similarity matching                 │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│   Hybrid Search                         │
│   - Vector search (semantic)            │
│   - Keyword search (exact match)        │
│   - Combine and rank results            │
└─────────────────────────────────────────┘
```

### Implementation Plan

**Step 1: Data Collection**
```python
# Collect venue data for popular cities
cities = ["San Francisco", "New York", "Seattle", "Austin"]
categories = ["restaurants", "parks", "museums", "cafes"]

for city in cities:
    for category in categories:
        venues = places_service.search_places(
            query=category,
            location=city,
            max_results=50
        )
        # Store in database
```

**Step 2: Generate Embeddings**
```python
from langchain_google_vertexai import VertexAIEmbeddings

embedding_model = VertexAIEmbeddings(model_name="text-embedding-005")

for venue in venues:
    # Create rich text representation
    text = f"{venue.name} - {venue.types} - {venue.address}"
    if venue.reviews:
        text += f" Reviews: {' '.join(r['text'] for r in venue.reviews[:3])}"
    
    # Generate embedding
    embedding = embedding_model.embed_query(text)
    
    # Store in vector DB
    vector_store.add(venue.place_id, embedding, metadata=venue.to_dict())
```

**Step 3: Semantic Search Tool**
```python
def semantic_venue_search_tool(query: str, location: str) -> str:
    """Search venues using semantic similarity."""
    
    # Generate query embedding
    query_embedding = embedding_model.embed_query(query)
    
    # Search vector store
    results = vector_store.similarity_search(
        query_embedding,
        k=10,
        filter={"location": location}
    )
    
    # Combine with live API results
    api_results = places_service.search_places(query, location)
    
    # Merge and rank
    combined = merge_and_rank(results, api_results)
    
    return format_results(combined)
```

**Step 4: Personalization**
```python
def personalized_recommendations_tool(user_id: str, activity_type: str) -> str:
    """Get personalized venue recommendations."""
    
    # Get user's past feedback
    feedback = get_user_feedback_history(user_id)
    
    # Extract preferences from feedback
    liked_venues = [f.venue_id for f in feedback if f.rating >= 4]
    
    # Find similar venues
    similar = []
    for venue_id in liked_venues:
        venue_embedding = vector_store.get_embedding(venue_id)
        similar.extend(
            vector_store.similarity_search(venue_embedding, k=5)
        )
    
    # Filter by activity type and rank
    recommendations = filter_and_rank(similar, activity_type)
    
    return format_recommendations(recommendations)
```

### Benefits of RAG

1. **Faster**: Cached data, no API calls for common queries
2. **Smarter**: Semantic understanding of "cozy Italian place"
3. **Personalized**: Learns from user feedback
4. **Cost-effective**: Reduces API calls
5. **Offline-capable**: Works without internet (cached data)

### Data Pipeline

```python
# Daily update job
def update_venue_cache():
    """Update venue cache with fresh data."""
    
    # Get popular venues
    venues = fetch_popular_venues()
    
    # Update embeddings
    for venue in venues:
        # Get latest details
        details = places_service.get_place_details(venue.place_id)
        
        # Regenerate embedding
        embedding = generate_embedding(details)
        
        # Update vector store
        vector_store.update(venue.place_id, embedding, details.to_dict())
    
    # Clean up old data
    vector_store.delete_old_entries(days=90)
```

## 🎨 Phase 3: Advanced Features

### Multi-Modal Search
- Search by uploaded photos
- "Find places that look like this"

### Group Consensus
- Analyze group preferences
- Find venues that satisfy everyone

### Contextual Recommendations
- Consider time of day
- Weather-aware suggestions
- Event type matching

### Social Integration
- Import from Google Maps saved places
- Share recommendations
- Collaborative lists

## 📊 Metrics to Track

1. **Search Quality**
   - Relevance of results
   - User satisfaction ratings
   - Click-through rates

2. **Performance**
   - Search latency
   - API call reduction
   - Cache hit rate

3. **Cost**
   - API usage
   - Vector DB costs
   - Embedding generation

## 🛠️ Tech Stack

- **Vector DB**: Vertex AI Vector Search
- **Embeddings**: text-embedding-005
- **API**: Google Places API
- **Caching**: Redis (optional)
- **Storage**: Cloud Storage for venue data
- **Monitoring**: Cloud Logging + BigQuery

## 🎯 Success Metrics

- 80% cache hit rate for common queries
- <500ms search latency
- 90% user satisfaction with recommendations
- 50% reduction in API costs

## 🚀 Getting Started with RAG

See the implementation in:
- `app/event_planning/rag_service.py` (coming soon)
- `app/event_planning/vector_store.py` (coming soon)
- `scripts/build_venue_cache.py` (coming soon)

For now, enjoy the direct API integration! 🎉
