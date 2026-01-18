/**
 * @file GrallocAllocator.h
 * @brief Gralloc-based buffer allocator implementation
 * 
 * Provides buffer allocation through the Android gralloc HAL,
 * supporting both gralloc 2.x and 3.x/4.x (AIDL) interfaces.
 */

#pragma once

#include "IBufferAllocator.h"
#include "BufferMapper.h"
#include <mutex>
#include <unordered_map>

namespace android {
namespace graphics {

// Forward declarations
class GrallocMapper;
class BufferCache;

/**
 * @brief Gralloc HAL version enumeration
 */
enum class GrallocVersion {
    GRALLOC_2_0,
    GRALLOC_3_0,
    GRALLOC_4_0,
    GRALLOC_AIDL
};

/**
 * @brief Gralloc-based allocator using Android HAL
 * 
 * Features:
 * - Automatic HAL version detection
 * - Buffer handle caching for performance
 * - Async allocation support via thread pool
 * - Format negotiation with gralloc
 * 
 * Thread Safety:
 * - All public methods are thread-safe
 * - Internal caching uses fine-grained locking
 * 
 * @note Requires libhidl or libbinder for HAL communication
 */
class GrallocAllocator : public IBufferAllocator {
public:
    /**
     * @brief Create allocator with automatic HAL detection
     */
    GrallocAllocator();
    
    /**
     * @brief Create allocator targeting specific HAL version
     * @param version Desired gralloc version
     */
    explicit GrallocAllocator(GrallocVersion version);
    
    ~GrallocAllocator() override;
    
    // IBufferAllocator implementation
    AllocationStatus allocate(
        const BufferDescriptor& descriptor,
        std::unique_ptr<GraphicBuffer>& outBuffer
    ) override;
    
    void allocateAsync(
        const BufferDescriptor& descriptor,
        AllocationCallback callback
    ) override;
    
    void free(GraphicBuffer* buffer) override;
    
    AllocationStatus importBuffer(
        const NativeHandle& handle,
        const BufferDescriptor& descriptor,
        std::unique_ptr<GraphicBuffer>& outBuffer
    ) override;
    
    BufferUsage getSupportedUsage() const override;
    
    bool isFormatSupported(
        PixelFormat format,
        BufferUsage usage
    ) const override;
    
    const char* getName() const override { return "GrallocAllocator"; }
    
    /**
     * @brief Get the detected gralloc version
     */
    GrallocVersion getVersion() const { return version_; }
    
    /**
     * @brief Get the underlying mapper for direct access
     */
    GrallocMapper* getMapper() const { return mapper_.get(); }
    
    /**
     * @brief Query implementation-defined format info
     * @param format Format to query
     * @param usage Intended usage
     * @param[out] outStride Stride in bytes
     * @return True if format is supported
     */
    bool queryFormatInfo(
        PixelFormat format,
        BufferUsage usage,
        uint32_t& outStride
    ) const;
    
    /**
     * @brief Dump allocator state for debugging
     */
    std::string dumpState() const;

private:
    GrallocVersion version_;
    std::unique_ptr<GrallocMapper> mapper_;
    std::unique_ptr<BufferCache> cache_;
    
    mutable std::mutex allocMutex_;
    std::unordered_map<uint64_t, GraphicBuffer*> activeBuffers_;
    
    // HAL-specific handles (opaque)
    void* halHandle_ = nullptr;
    
    bool initializeHal();
    void shutdownHal();
    
    AllocationStatus allocateInternal(
        const BufferDescriptor& descriptor,
        NativeHandle& outHandle
    );
};

/**
 * @brief Gralloc buffer mapper for CPU access
 * 
 * Handles lock/unlock operations for gralloc buffers,
 * abstracting differences between gralloc versions.
 */
class GrallocMapper {
public:
    explicit GrallocMapper(GrallocVersion version);
    ~GrallocMapper();
    
    /**
     * @brief Lock a buffer for CPU access
     * @param handle Native buffer handle
     * @param usage CPU access mode
     * @param region Rectangle to lock (nullptr = entire buffer)
     * @param[out] outData Pointer to mapped data
     * @return True on success
     */
    bool lock(
        const NativeHandle& handle,
        BufferUsage usage,
        const MappedRegion* region,
        void** outData
    );
    
    /**
     * @brief Unlock a previously locked buffer
     * @param handle Buffer to unlock
     * @param[out] outFence Fence FD for async unlock (may be -1)
     * @return True on success
     */
    bool unlock(const NativeHandle& handle, int* outFence = nullptr);
    
    /**
     * @brief Get buffer metadata
     * @param handle Buffer handle
     * @param metadataType Type of metadata to retrieve
     * @param[out] outData Metadata buffer
     * @param[in,out] size In: buffer size, Out: data size
     * @return True on success
     */
    bool getMetadata(
        const NativeHandle& handle,
        uint32_t metadataType,
        void* outData,
        size_t& size
    );

private:
    GrallocVersion version_;
    void* mapperHandle_ = nullptr;
};

} // namespace graphics
} // namespace android
