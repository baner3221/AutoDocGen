/**
 * @file BufferCache.h
 * @brief LRU cache for frequently used buffer handles
 * 
 * Provides caching to reduce gralloc HAL calls for repeated
 * import/validation operations.
 */

#pragma once

#include "BufferTypes.h"
#include <memory>
#include <unordered_map>
#include <list>
#include <mutex>

namespace android {
namespace graphics {

// Forward declarations
class GraphicBuffer;

/**
 * @brief Cache entry for buffer metadata
 */
struct BufferCacheEntry {
    uint64_t bufferId = 0;
    BufferDescriptor descriptor;
    NativeHandle handle;
    uint64_t lastAccessTime = 0;
    uint32_t accessCount = 0;
    bool isValid = true;
};

/**
 * @brief LRU cache for buffer handles and metadata
 * 
 * Features:
 * - Configurable capacity
 * - LRU eviction policy
 * - Thread-safe access
 * - Automatic invalidation on buffer free
 * 
 * @see GrallocAllocator for cache integration
 */
class BufferCache {
public:
    /**
     * @brief Create a cache with maximum capacity
     * @param maxEntries Maximum cached entries
     */
    explicit BufferCache(size_t maxEntries = 64);
    
    ~BufferCache();
    
    /**
     * @brief Look up a buffer by ID
     * @param bufferId Buffer identifier
     * @return Cached entry or nullptr if not found
     */
    const BufferCacheEntry* lookup(uint64_t bufferId) const;
    
    /**
     * @brief Insert or update a cache entry
     * @param entry Entry to cache
     */
    void insert(const BufferCacheEntry& entry);
    
    /**
     * @brief Invalidate a specific entry
     * @param bufferId Buffer to invalidate
     * @return True if entry was found and removed
     */
    bool invalidate(uint64_t bufferId);
    
    /**
     * @brief Clear all cache entries
     */
    void clear();
    
    /**
     * @brief Get current cache size
     */
    size_t size() const;
    
    /**
     * @brief Get cache hit statistics
     * @return Hit rate (0.0 to 1.0)
     */
    double getHitRate() const;
    
    /**
     * @brief Resize the cache
     * @param newMaxEntries New maximum capacity
     */
    void resize(size_t newMaxEntries);

private:
    size_t maxEntries_;
    
    // LRU list (front = most recent)
    std::list<BufferCacheEntry> entries_;
    
    // Map for O(1) lookup
    std::unordered_map<uint64_t, std::list<BufferCacheEntry>::iterator> indexMap_;
    
    mutable std::mutex mutex_;
    
    // Statistics
    mutable uint64_t hits_ = 0;
    mutable uint64_t misses_ = 0;
    
    void evictLRU();
    void moveToFront(std::list<BufferCacheEntry>::iterator it);
};

} // namespace graphics
} // namespace android
