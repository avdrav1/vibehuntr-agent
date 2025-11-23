"""Unit tests for metadata cache service."""

import asyncio
import pytest
from backend.app.services.metadata_cache import MetadataCache
from backend.app.models.link_preview import LinkMetadata


@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return LinkMetadata(
        url="https://example.com",
        domain="example.com",
        title="Example Title",
        description="Example description",
        image="https://example.com/image.jpg",
        favicon="https://example.com/favicon.ico",
        error=None
    )


@pytest.fixture
def cache():
    """Create a cache instance for testing."""
    return MetadataCache(ttl=3600, max_size=1000)


@pytest.mark.asyncio
async def test_cache_hit_returns_cached_data(cache, sample_metadata):
    """Test that cache hit returns the cached data.
    
    Requirements: 3.5
    """
    url = "https://example.com"
    
    # Set metadata in cache
    await cache.set(url, sample_metadata)
    
    # Retrieve from cache
    cached = await cache.get(url)
    
    # Should return the cached metadata
    assert cached is not None
    assert cached.url == sample_metadata.url
    assert cached.domain == sample_metadata.domain
    assert cached.title == sample_metadata.title
    assert cached.description == sample_metadata.description
    assert cached.image == sample_metadata.image
    assert cached.favicon == sample_metadata.favicon


@pytest.mark.asyncio
async def test_cache_miss_returns_none(cache):
    """Test that cache miss returns None.
    
    Requirements: 3.5
    """
    url = "https://nonexistent.com"
    
    # Try to get non-existent URL
    cached = await cache.get(url)
    
    # Should return None
    assert cached is None


@pytest.mark.asyncio
async def test_cache_expiration_after_ttl(sample_metadata):
    """Test that cache entries expire after TTL.
    
    Requirements: 3.5
    """
    # Create cache with short TTL (1 second)
    cache = MetadataCache(ttl=1, max_size=1000)
    url = "https://example.com"
    
    # Set metadata in cache
    await cache.set(url, sample_metadata)
    
    # Immediately retrieve - should be cached
    cached = await cache.get(url)
    assert cached is not None
    
    # Wait for TTL to expire
    await asyncio.sleep(1.1)
    
    # Should now return None (expired)
    cached = await cache.get(url)
    assert cached is None


@pytest.mark.asyncio
async def test_lru_eviction_when_cache_full():
    """Test that LRU eviction occurs when cache is full.
    
    Requirements: 3.5
    """
    # Create cache with small max size
    cache = MetadataCache(ttl=3600, max_size=3)
    
    # Create test metadata
    metadata1 = LinkMetadata(url="https://example1.com", domain="example1.com")
    metadata2 = LinkMetadata(url="https://example2.com", domain="example2.com")
    metadata3 = LinkMetadata(url="https://example3.com", domain="example3.com")
    metadata4 = LinkMetadata(url="https://example4.com", domain="example4.com")
    
    # Fill cache to capacity
    await cache.set("https://example1.com", metadata1)
    await cache.set("https://example2.com", metadata2)
    await cache.set("https://example3.com", metadata3)
    
    # All three should be cached
    assert await cache.get("https://example1.com") is not None
    assert await cache.get("https://example2.com") is not None
    assert await cache.get("https://example3.com") is not None
    
    # Add fourth entry (should evict first one - LRU)
    await cache.set("https://example4.com", metadata4)
    
    # First entry should be evicted
    assert await cache.get("https://example1.com") is None
    
    # Other entries should still be cached
    assert await cache.get("https://example2.com") is not None
    assert await cache.get("https://example3.com") is not None
    assert await cache.get("https://example4.com") is not None


@pytest.mark.asyncio
async def test_lru_ordering_with_access():
    """Test that accessing an entry updates its LRU position.
    
    Requirements: 3.5
    """
    # Create cache with small max size
    cache = MetadataCache(ttl=3600, max_size=3)
    
    # Create test metadata
    metadata1 = LinkMetadata(url="https://example1.com", domain="example1.com")
    metadata2 = LinkMetadata(url="https://example2.com", domain="example2.com")
    metadata3 = LinkMetadata(url="https://example3.com", domain="example3.com")
    metadata4 = LinkMetadata(url="https://example4.com", domain="example4.com")
    
    # Fill cache
    await cache.set("https://example1.com", metadata1)
    await cache.set("https://example2.com", metadata2)
    await cache.set("https://example3.com", metadata3)
    
    # Access first entry (moves it to end of LRU)
    await cache.get("https://example1.com")
    
    # Add fourth entry (should evict second one, not first)
    await cache.set("https://example4.com", metadata4)
    
    # First entry should still be cached (was accessed recently)
    assert await cache.get("https://example1.com") is not None
    
    # Second entry should be evicted (was least recently used)
    assert await cache.get("https://example2.com") is None
    
    # Third and fourth should be cached
    assert await cache.get("https://example3.com") is not None
    assert await cache.get("https://example4.com") is not None


@pytest.mark.asyncio
async def test_cache_update_existing_entry():
    """Test that updating an existing entry works correctly.
    
    Requirements: 3.5
    """
    cache = MetadataCache(ttl=3600, max_size=1000)
    url = "https://example.com"
    
    # Set initial metadata
    metadata1 = LinkMetadata(
        url=url,
        domain="example.com",
        title="Original Title"
    )
    await cache.set(url, metadata1)
    
    # Update with new metadata
    metadata2 = LinkMetadata(
        url=url,
        domain="example.com",
        title="Updated Title"
    )
    await cache.set(url, metadata2)
    
    # Should return updated metadata
    cached = await cache.get(url)
    assert cached is not None
    assert cached.title == "Updated Title"


@pytest.mark.asyncio
async def test_cache_clear():
    """Test that clear() removes all entries.
    
    Requirements: 3.5
    """
    cache = MetadataCache(ttl=3600, max_size=1000)
    
    # Add multiple entries
    metadata1 = LinkMetadata(url="https://example1.com", domain="example1.com")
    metadata2 = LinkMetadata(url="https://example2.com", domain="example2.com")
    metadata3 = LinkMetadata(url="https://example3.com", domain="example3.com")
    
    await cache.set("https://example1.com", metadata1)
    await cache.set("https://example2.com", metadata2)
    await cache.set("https://example3.com", metadata3)
    
    # Verify entries are cached
    assert await cache.get("https://example1.com") is not None
    assert await cache.get("https://example2.com") is not None
    assert await cache.get("https://example3.com") is not None
    
    # Clear cache
    await cache.clear()
    
    # All entries should be gone
    assert await cache.get("https://example1.com") is None
    assert await cache.get("https://example2.com") is None
    assert await cache.get("https://example3.com") is None


@pytest.mark.asyncio
async def test_thread_safety_concurrent_access():
    """Test thread safety with concurrent access.
    
    Requirements: 3.5
    """
    cache = MetadataCache(ttl=3600, max_size=1000)
    
    # Create multiple metadata objects
    metadatas = [
        LinkMetadata(url=f"https://example{i}.com", domain=f"example{i}.com")
        for i in range(10)
    ]
    
    # Concurrent set operations
    async def set_metadata(i):
        await cache.set(f"https://example{i}.com", metadatas[i])
    
    # Run concurrent sets
    await asyncio.gather(*[set_metadata(i) for i in range(10)])
    
    # All entries should be cached
    for i in range(10):
        cached = await cache.get(f"https://example{i}.com")
        assert cached is not None
        assert cached.domain == f"example{i}.com"


@pytest.mark.asyncio
async def test_thread_safety_concurrent_get_and_set():
    """Test thread safety with concurrent get and set operations.
    
    Requirements: 3.5
    """
    cache = MetadataCache(ttl=3600, max_size=1000)
    url = "https://example.com"
    
    metadata = LinkMetadata(url=url, domain="example.com", title="Test")
    
    # Set initial value
    await cache.set(url, metadata)
    
    # Concurrent get and set operations
    async def get_metadata():
        return await cache.get(url)
    
    async def set_metadata():
        new_metadata = LinkMetadata(url=url, domain="example.com", title="Updated")
        await cache.set(url, new_metadata)
    
    # Run concurrent operations
    results = await asyncio.gather(
        get_metadata(),
        set_metadata(),
        get_metadata(),
        set_metadata(),
        get_metadata()
    )
    
    # All get operations should return valid metadata (not None)
    for result in [results[0], results[2], results[4]]:
        assert result is not None
        assert result.url == url


@pytest.mark.asyncio
async def test_cache_with_partial_metadata():
    """Test caching metadata with only some fields populated.
    
    Requirements: 3.5
    """
    cache = MetadataCache(ttl=3600, max_size=1000)
    url = "https://example.com"
    
    # Create metadata with only required fields
    metadata = LinkMetadata(
        url=url,
        domain="example.com",
        title=None,
        description=None,
        image=None,
        favicon=None
    )
    
    await cache.set(url, metadata)
    
    # Should be able to retrieve partial metadata
    cached = await cache.get(url)
    assert cached is not None
    assert cached.url == url
    assert cached.domain == "example.com"
    assert cached.title is None
    assert cached.description is None


@pytest.mark.asyncio
async def test_cache_with_error_metadata():
    """Test caching metadata with error field populated.
    
    Requirements: 3.5
    """
    cache = MetadataCache(ttl=3600, max_size=1000)
    url = "https://example.com"
    
    # Create metadata with error
    metadata = LinkMetadata(
        url=url,
        domain="example.com",
        error="Failed to fetch"
    )
    
    await cache.set(url, metadata)
    
    # Should be able to retrieve error metadata
    cached = await cache.get(url)
    assert cached is not None
    assert cached.url == url
    assert cached.error == "Failed to fetch"
