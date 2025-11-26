"""Metadata caching service for link previews.

This module provides an in-memory cache for link metadata with TTL and LRU eviction.
"""

import asyncio
import time
from collections import OrderedDict
from typing import Optional

from backend.app.models.link_preview import LinkMetadata


class MetadataCache:
    """In-memory cache for link metadata with TTL and LRU eviction.
    
    This cache is thread-safe using asyncio locks and implements:
    - Time-to-live (TTL) expiration
    - Least Recently Used (LRU) eviction when cache is full
    - Async get/set operations
    """
    
    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        """Initialize the metadata cache.
        
        Args:
            ttl: Time-to-live in seconds (default: 3600 = 1 hour)
            max_size: Maximum number of entries (default: 1000)
        """
        self.ttl = ttl
        self.max_size = max_size
        self._cache: OrderedDict[str, tuple[LinkMetadata, float]] = OrderedDict()
        self._lock = asyncio.Lock()
    
    async def get(self, url: str) -> Optional[LinkMetadata]:
        """Get cached metadata for a URL.
        
        Args:
            url: The URL to look up
            
        Returns:
            LinkMetadata if found and not expired, None otherwise
        """
        async with self._lock:
            if url not in self._cache:
                return None
            
            metadata, timestamp = self._cache[url]
            
            # Check if entry has expired
            if time.time() - timestamp > self.ttl:
                # Remove expired entry
                del self._cache[url]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(url)
            
            return metadata
    
    async def set(self, url: str, metadata: LinkMetadata) -> None:
        """Cache metadata for a URL.
        
        Args:
            url: The URL to cache
            metadata: The metadata to store
        """
        async with self._lock:
            # If URL already exists, remove it first (will be re-added at end)
            if url in self._cache:
                del self._cache[url]
            
            # If cache is full, remove least recently used entry
            if len(self._cache) >= self.max_size:
                # Remove first item (least recently used)
                self._cache.popitem(last=False)
            
            # Add new entry with current timestamp
            self._cache[url] = (metadata, time.time())
    
    async def clear(self) -> None:
        """Clear all cached metadata."""
        async with self._lock:
            self._cache.clear()
