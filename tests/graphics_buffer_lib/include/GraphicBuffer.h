/**
 * @file GraphicBuffer.h
 * @brief Core buffer class representing an allocated graphics buffer
 * 
 * GraphicBuffer is the primary class for managing graphics memory.
 * It wraps native handles and provides CPU/GPU access methods.
 */

#pragma once

#include "BufferTypes.h"
#include <memory>
#include <mutex>
#include <atomic>

namespace android {
namespace graphics {

// Forward declarations
class IBufferAllocator;
class BufferMapper;
class FenceManager;

/**
 * @brief Represents an allocated graphics buffer
 * 
 * GraphicBuffer provides:
 * - CPU mapping (lock/unlock)
 * - GPU resource binding
 * - Reference counting
 * - Fence synchronization
 * 
 * Thread Safety:
 * - Lock/unlock operations are serialized
 * - Reference counting is atomic
 * - Handle duplication is thread-safe
 * 
 * @see BufferPool for buffer lifecycle management
 * @see BufferMapper for CPU access helpers
 */
class GraphicBuffer {
public:
    /**
     * @brief Construct a buffer with the given properties
     * @param descriptor Buffer geometry and format
     * @param handle Native buffer handle from allocator
     * @param allocator The allocator that created this buffer
     */
    GraphicBuffer(
        const BufferDescriptor& descriptor,
        NativeHandle handle,
        IBufferAllocator* allocator
    );
    
    /**
     * @brief Move constructor
     */
    GraphicBuffer(GraphicBuffer&& other) noexcept;
    
    /**
     * @brief Destructor - releases the buffer back to allocator
     */
    ~GraphicBuffer();
    
    // Non-copyable
    GraphicBuffer(const GraphicBuffer&) = delete;
    GraphicBuffer& operator=(const GraphicBuffer&) = delete;
    
    /**
     * @brief Lock the buffer for CPU read access
     * @param[out] outRegion Pointer to receive mapped memory info
     * @return True if lock succeeded
     */
    bool lockForRead(MappedRegion& outRegion);
    
    /**
     * @brief Lock the buffer for CPU write access
     * @param[out] outRegion Pointer to receive mapped memory info
     * @return True if lock succeeded
     */
    bool lockForWrite(MappedRegion& outRegion);
    
    /**
     * @brief Lock a specific region for CPU access
     * @param x Left edge of region
     * @param y Top edge of region
     * @param width Region width
     * @param height Region height
     * @param[out] outRegion Mapped memory info
     * @return True if lock succeeded
     */
    bool lockRegion(
        uint32_t x, uint32_t y,
        uint32_t width, uint32_t height,
        MappedRegion& outRegion
    );
    
    /**
     * @brief Unlock the buffer, flushing any writes
     * @return True if unlock succeeded
     */
    bool unlock();
    
    /**
     * @brief Get a duplicate native handle for sharing
     * @return Duplicated handle (caller owns)
     */
    NativeHandle duplicateHandle() const;
    
    /**
     * @brief Increment reference count
     */
    void incRef();
    
    /**
     * @brief Decrement reference count
     * @return True if buffer should be deleted
     */
    bool decRef();
    
    /**
     * @brief Get current reference count
     */
    int32_t getRefCount() const;
    
    // Accessors
    const BufferDescriptor& getDescriptor() const { return descriptor_; }
    uint32_t getWidth() const { return descriptor_.width; }
    uint32_t getHeight() const { return descriptor_.height; }
    uint32_t getStride() const { return descriptor_.stride; }
    PixelFormat getFormat() const { return descriptor_.format; }
    BufferUsage getUsage() const { return descriptor_.usage; }
    const NativeHandle& getNativeHandle() const { return handle_; }
    bool isLocked() const { return mappedRegion_.isLocked(); }
    
    /**
     * @brief Get unique buffer ID for debugging
     */
    uint64_t getBufferId() const { return bufferId_; }
    
    /**
     * @brief Set an associated fence for synchronization
     * @param fenceManager Fence manager instance
     * @param fenceFd Fence file descriptor
     */
    void setAcquireFence(FenceManager* fenceManager, int fenceFd);
    
    /**
     * @brief Wait for acquire fence to signal
     * @param timeoutMs Maximum wait time in milliseconds
     * @return True if fence signaled, false on timeout
     */
    bool waitAcquireFence(uint32_t timeoutMs);

private:
    BufferDescriptor descriptor_;
    NativeHandle handle_;
    IBufferAllocator* allocator_;
    MappedRegion mappedRegion_;
    
    std::atomic<int32_t> refCount_{1};
    std::mutex lockMutex_;
    
    uint64_t bufferId_;
    static std::atomic<uint64_t> nextBufferId_;
    
    // Fence synchronization
    FenceManager* fenceManager_ = nullptr;
    int acquireFenceFd_ = -1;
    
    friend class BufferMapper;
    friend class BufferPool;
};

} // namespace graphics
} // namespace android
