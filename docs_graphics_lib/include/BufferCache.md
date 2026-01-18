# BufferCache.h

---

| Property | Value |
|----------|-------|
| **Location** | `include\BufferCache.h` |
| **Lines** | 118 |
| **Classes** | 2 |
| **Functions** | 0 |
| **Last Updated** | 2026-01-18 13:28 |

---

## Quick Navigation

### Classes
- [android::graphics::BufferCacheEntry](#android-graphics-buffercacheentry)
- [android::graphics::BufferCache](#android-graphics-buffercache)

---

## Documentation for `BufferCache.h`

### 1. Comprehensive Description (2-4 paragraphs)
The `BufferCache` class is designed to provide an efficient LRU (Least Recently Used) cache for frequently used buffer handles and their metadata. This cache helps reduce the number of gralloc HAL calls by caching buffer import/validation operations, which can be time-consuming and resource-intensive.

The cache supports configurable capacity and uses a combination of a linked list and an unordered map to achieve O(1) average time complexity for lookups, insertions, and invalidations. The LRU eviction policy ensures that the least recently accessed buffers are evicted when the cache reaches its maximum capacity.

This class is particularly useful in scenarios where buffer management is critical, such as in graphics rendering or audio processing applications, where repeated access to the same buffers is common.

### 2. Parameters (DETAILED for each)
#### `BufferCache(size_t maxEntries = 64)`
- **Purpose**: Initializes a new instance of the `BufferCache` class with a specified maximum capacity.
- **Type Semantics**: A size_t value representing the maximum number of entries that can be stored in the cache.
- **Valid Values**: Any non-negative integer.
- **Ownership**: The caller owns the memory for the `BufferCache` object.
- **Nullability**: Not applicable.

#### `lookup(uint64_t bufferId) const`
- **Purpose**: Retrieves a cached entry based on the provided buffer identifier.
- **Type Semantics**: A pointer to a `BufferCacheEntry`.
- **Valid Values**: Any valid buffer ID.
- **Ownership**: The returned pointer is owned by the cache and should not be deleted by the caller.
- **Nullability**: Returns nullptr if no entry with the specified buffer ID exists in the cache.

#### `insert(const BufferCacheEntry& entry)`
- **Purpose**: Inserts or updates a cache entry with the provided metadata.
- **Type Semantics**: A reference to a `BufferCacheEntry`.
- **Valid Values**: Any valid `BufferCacheEntry` object.
- **Ownership**: The caller retains ownership of the `BufferCacheEntry` object.
- **Nullability**: Not applicable.

#### `invalidate(uint64_t bufferId)`
- **Purpose**: Invalidates a specific cache entry based on the provided buffer identifier.
- **Type Semantics**: A boolean value indicating whether the entry was found and removed from the cache.
- **Valid Values**: True if the entry exists and is successfully invalidated, false otherwise.
- **Ownership**: The caller retains ownership of the `BufferCacheEntry` object.
- **Nullability**: Not applicable.

#### `clear()`
- **Purpose**: Clears all entries from the cache.
- **Type Semantics**: Void.
- **Valid Values**: None.
- **Ownership**: No memory is released by this operation.
- **Nullability**: Not applicable.

#### `size() const`
- **Purpose**: Returns the current number of entries in the cache.
- **Type Semantics**: A size_t value representing the number of entries.
- **Valid Values**: Any non-negative integer.
- **Ownership**: No memory is released by this operation.
- **Nullability**: Not applicable.

#### `getHitRate() const`
- **Purpose**: Calculates and returns the hit rate of the cache, which measures the proportion of successful lookups.
- **Type Semantics**: A double value representing the hit rate (0.0 to 1.0).
- **Valid Values**: Any floating-point number between 0.0 and 1.0.
- **Ownership**: No memory is released by this operation.
- **Nullability**: Not applicable.

#### `resize(size_t newMaxEntries)`
- **Purpose**: Resizes the cache to a new maximum capacity.
- **Type Semantics**: A size_t value representing the new maximum number of entries.
- **Valid Values**: Any non-negative integer.
- **Ownership**: No memory is released by this operation.
- **Nullability**: Not applicable.

### 3. Return Value
#### `lookup(uint64_t bufferId) const`
- **Purpose**: Returns a pointer to a `BufferCacheEntry` if found, otherwise returns nullptr.
- **Type Semantics**: A pointer to a `BufferCacheEntry`.
- **Valid Values**: A valid `BufferCacheEntry` object or nullptr.
- **Ownership**: The returned pointer is owned by the cache and should not be deleted by the caller.
- **Nullability**: Returns nullptr if no entry with the specified buffer ID exists in the cache.

#### `insert(const BufferCacheEntry& entry)`
- **Purpose**: Inserts or updates a cache entry.
- **Type Semantics**: A boolean value indicating whether the insertion was successful.
- **Valid Values**: True if the entry was successfully inserted or updated, false otherwise.
- **Ownership**: The caller retains ownership of the `BufferCacheEntry` object.
- **Nullability**: Not applicable.

#### `invalidate(uint64_t bufferId)`
- **Purpose**: Invalidates a cache entry.
- **Type Semantics**: A boolean value indicating whether the entry was found and removed from the cache.
- **Valid Values**: True if the entry exists and is successfully invalidated, false otherwise.
- **Ownership**: The caller retains ownership of the `BufferCacheEntry` object.
- **Nullability**: Not applicable.

#### `clear()`
- **Purpose**: Clears all entries from the cache.
- **Type Semantics**: Void.
- **Valid Values**: None.
- **Ownership**: No memory is released by this operation.
- **Nullability**: Not applicable.

#### `size() const`
- **Purpose**: Returns the current number of entries in the cache.
- **Type Semantics**: A size_t value representing the number of entries.
- **Valid Values**: Any non-negative integer.
- **Ownership**: No memory is released by this operation.
- **Nullability**: Not applicable.

#### `getHitRate() const`
- **Purpose**: Calculates and returns the hit rate of the cache.
- **Type Semantics**: A double value representing the hit rate (0.0 to 1.0).
- **Valid Values**: Any floating-point number between 0.0 and 1.0.
- **Ownership**: No memory is released by this operation.
- **Nullability**: Not applicable.

#### `resize(size_t newMaxEntries)`
- **Purpose**: Resizes the cache to a new maximum capacity.
- **Type Semantics**: Void.
- **Valid Values**: None.
- **Ownership**: No memory is released by this operation.
- **Nullability**: Not applicable.

### 4. Dependencies Cross-Reference
The `BufferCache` class does not depend on any external classes or functions in the provided code snippet.

### 5. Side Effects
#### `lookup(uint64_t bufferId) const`
- State modifications: None.
- Locks acquired/released: The cache is accessed using a mutex to ensure thread safety.
- I/O operations: No I/O operations are performed.
- Signals/events emitted: No signals or events are emitted.

#### `insert(const BufferCacheEntry& entry)`
- State modifications: The cache is updated with the new entry, potentially evicting an existing entry if necessary.
- Locks acquired/released: The cache is accessed using a mutex to ensure thread safety.
- I/O operations: No I/O operations are performed.
- Signals/events emitted: No signals or events are emitted.

#### `invalidate(uint64_t bufferId)`
- State modifications: An existing entry with the specified buffer ID is removed from the cache.
- Locks acquired/released: The cache is accessed using a mutex to ensure thread safety.
- I/O operations: No I/O operations are performed.
- Signals/events emitted: No signals or events are emitted.

#### `clear()`
- State modifications: All entries in the cache are removed.
- Locks acquired/released: The cache is accessed using a mutex to ensure thread safety.
- I/O operations: No I/O operations are performed.
- Signals/events emitted: No signals or events are emitted.

#### `size() const`
- State modifications: None.
- Locks acquired/released: The cache is accessed using a mutex to ensure thread safety.
- I/O operations: No I/O operations are performed.
- Signals/events emitted: No signals or events are emitted.

#### `getHitRate() const`
- State modifications: None.
- Locks acquired/released: The cache is accessed using a mutex to ensure thread safety.
- I/O operations: No I/O operations are performed.
- Signals/events emitted: No signals or events are emitted.

#### `resize(size_t newMaxEntries)`
- State modifications: The maximum capacity of the cache is updated.
- Locks acquired/released: The cache is accessed using a mutex to ensure thread safety.
- I/O operations: No I/O operations are performed.
- Signals/events emitted: No signals or events are emitted.

### 6. Usage Context
The `BufferCache` class should be used in scenarios where buffer management is critical, such as in graphics rendering or audio processing applications. It can be integrated into the GrallocAllocator to reduce the number of gralloc HAL calls by caching buffer import/validation operations.

### 7. Related Functions
| Relationship Type | Function Name |
|------------------|--------------|
| Uses             | BufferCacheEntry |

### 8. Code Example

```cpp
#include "BufferCache.h"
#include <android/log.h>

int main() {
    android::graphics::BufferCache cache(10);

    // Create a buffer descriptor and handle
    android::graphics::BufferDescriptor desc;
    android::native_handle_t* handle = new android::native_handle_t[2];
    handle[0].data = (void*)0x12345678;
    handle[0].size = 4096;
    handle[0].type = ANDROID_HANDLE_TYPE_MMAP;
    handle