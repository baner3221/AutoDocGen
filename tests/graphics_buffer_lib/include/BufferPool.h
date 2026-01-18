/**
 * @file BufferPool.h
 * @brief High-performance buffer pool for buffer reuse
 * 
 * BufferPool manages a collection of pre-allocated buffers to reduce
 * allocation latency in camera streaming and video playback scenarios.
 */

#pragma once

#include "BufferTypes.h"
#include "GraphicBuffer.h"
#include "IBufferAllocator.h"
#include <memory>
#include <vector>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <functional>

namespace android {
namespace graphics {

// Forward declarations
class BufferPoolListener;
class CameraBufferManager;

/**
 * @brief Configuration for buffer pool behavior
 */
struct BufferPoolConfig {
    uint32_t minBuffers = 3;        ///< Minimum buffers to keep allocated
    uint32_t maxBuffers = 10;       ///< Maximum buffers allowed
    uint32_t preAllocate = 4;       ///< Buffers to allocate on creation
    uint32_t growthCount = 2;       ///< Buffers to add when pool is empty
    bool allowBlocking = true;      ///< Block on acquire if pool empty
    uint32_t blockTimeoutMs = 1000; ///< Timeout for blocking acquire
};

/**
 * @brief High-performance buffer pool with lifecycle management
 * 
 * Features:
 * - Pre-allocation for reduced latency
 * - Automatic pool growth
 * - Buffer reuse with format validation
 * - Statistics collection
 * - Listener callbacks for pool events
 * 
 * Usage:
 * @code
 * BufferPool pool(allocator, descriptor, config);
 * 
 * // Acquire a buffer
 * GraphicBuffer* buf = pool.acquireBuffer();
 * 
 * // Use buffer...
 * 
 * // Release back to pool
 * pool.releaseBuffer(buf);
 * @endcode
 * 
 * @see CameraBufferManager for camera-specific pooling
 */
class BufferPool {
public:
    /**
     * @brief Create a buffer pool
     * @param allocator Allocator to use for buffer creation
     * @param descriptor Buffer format for all pool buffers
     * @param config Pool behavior configuration
     */
    BufferPool(
        std::shared_ptr<IBufferAllocator> allocator,
        const BufferDescriptor& descriptor,
        const BufferPoolConfig& config = BufferPoolConfig()
    );
    
    /**
     * @brief Destructor - frees all pooled buffers
     */
    ~BufferPool();
    
    // Non-copyable, non-movable
    BufferPool(const BufferPool&) = delete;
    BufferPool& operator=(const BufferPool&) = delete;
    
    /**
     * @brief Acquire a buffer from the pool
     * 
     * If no buffers are available:
     * - Attempts to grow the pool if under maxBuffers
     * - Blocks if allowBlocking is true
     * - Returns nullptr on timeout or if pool cannot grow
     * 
     * @return Buffer pointer (still owned by pool) or nullptr
     */
    GraphicBuffer* acquireBuffer();
    
    /**
     * @brief Acquire with custom timeout
     * @param timeoutMs Maximum wait time (0 = non-blocking)
     * @return Buffer pointer or nullptr
     */
    GraphicBuffer* acquireBuffer(uint32_t timeoutMs);
    
    /**
     * @brief Release a buffer back to the pool
     * @param buffer Previously acquired buffer
     */
    void releaseBuffer(GraphicBuffer* buffer);
    
    /**
     * @brief Pre-allocate additional buffers
     * @param count Number of buffers to add
     * @return Number successfully allocated
     */
    uint32_t grow(uint32_t count);
    
    /**
     * @brief Release unused buffers to reduce memory
     * @param keepCount Minimum free buffers to retain
     * @return Number of buffers freed
     */
    uint32_t shrink(uint32_t keepCount = 0);
    
    /**
     * @brief Flush all buffers (blocks until all returned)
     * @param timeoutMs Maximum wait time
     * @return True if all buffers returned
     */
    bool flush(uint32_t timeoutMs = 5000);
    
    /**
     * @brief Get current pool statistics
     */
    PoolStatistics getStatistics() const;
    
    /**
     * @brief Add a listener for pool events
     */
    void addListener(BufferPoolListener* listener);
    
    /**
     * @brief Remove a previously added listener
     */
    void removeListener(BufferPoolListener* listener);
    
    // Accessors
    const BufferDescriptor& getDescriptor() const { return descriptor_; }
    uint32_t getFreeCount() const;
    uint32_t getTotalCount() const;
    bool isFull() const;
    bool isEmpty() const;

private:
    std::shared_ptr<IBufferAllocator> allocator_;
    BufferDescriptor descriptor_;
    BufferPoolConfig config_;
    
    std::vector<std::unique_ptr<GraphicBuffer>> allBuffers_;
    std::queue<GraphicBuffer*> freeBuffers_;
    
    mutable std::mutex mutex_;
    std::condition_variable bufferAvailable_;
    
    std::vector<BufferPoolListener*> listeners_;
    PoolStatistics stats_;
    
    void notifyBufferAcquired(GraphicBuffer* buffer);
    void notifyBufferReleased(GraphicBuffer* buffer);
    void notifyPoolGrew(uint32_t newTotal);
    void notifyPoolShrunk(uint32_t newTotal);
};

/**
 * @brief Listener interface for buffer pool events
 */
class BufferPoolListener {
public:
    virtual ~BufferPoolListener() = default;
    
    virtual void onBufferAcquired(BufferPool* pool, GraphicBuffer* buffer) {}
    virtual void onBufferReleased(BufferPool* pool, GraphicBuffer* buffer) {}
    virtual void onPoolGrew(BufferPool* pool, uint32_t newTotal) {}
    virtual void onPoolShrunk(BufferPool* pool, uint32_t newTotal) {}
    virtual void onPoolExhausted(BufferPool* pool) {}
};

} // namespace graphics
} // namespace android
