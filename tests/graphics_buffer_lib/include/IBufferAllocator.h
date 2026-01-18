/**
 * @file IBufferAllocator.h
 * @brief Abstract interface for buffer allocation strategies
 * 
 * Provides the core abstraction for different allocation backends
 * (gralloc, ION, dmabuf heaps, etc.)
 */

#pragma once

#include "BufferTypes.h"
#include <memory>
#include <functional>

namespace android {
namespace graphics {

// Forward declarations
class GraphicBuffer;
class BufferPool;

/**
 * @brief Abstract buffer allocator interface
 * 
 * Implementations include:
 * - GrallocAllocator: Standard Android gralloc backend
 * - IonAllocator: Legacy ION memory allocator
 * - DmaBufHeapAllocator: Modern dmabuf heaps backend
 * 
 * @note Allocators are thread-safe and can be shared across BufferPools
 */
class IBufferAllocator {
public:
    using AllocationCallback = std::function<void(AllocationStatus, GraphicBuffer*)>;
    
    virtual ~IBufferAllocator() = default;
    
    /**
     * @brief Allocate a new graphic buffer
     * @param descriptor Buffer geometry and usage requirements
     * @param[out] outBuffer Pointer to receive allocated buffer
     * @return Status code indicating success or failure reason
     */
    virtual AllocationStatus allocate(
        const BufferDescriptor& descriptor,
        std::unique_ptr<GraphicBuffer>& outBuffer
    ) = 0;
    
    /**
     * @brief Asynchronously allocate a buffer
     * @param descriptor Buffer requirements
     * @param callback Called when allocation completes
     */
    virtual void allocateAsync(
        const BufferDescriptor& descriptor,
        AllocationCallback callback
    ) = 0;
    
    /**
     * @brief Free a previously allocated buffer
     * @param buffer Buffer to release
     */
    virtual void free(GraphicBuffer* buffer) = 0;
    
    /**
     * @brief Import a buffer from a native handle
     * @param handle External native handle
     * @param descriptor Expected buffer properties
     * @param[out] outBuffer Imported buffer
     * @return Status code
     */
    virtual AllocationStatus importBuffer(
        const NativeHandle& handle,
        const BufferDescriptor& descriptor,
        std::unique_ptr<GraphicBuffer>& outBuffer
    ) = 0;
    
    /**
     * @brief Get allocator capabilities
     * @return Bitmask of supported BufferUsage flags
     */
    virtual BufferUsage getSupportedUsage() const = 0;
    
    /**
     * @brief Check if format is supported with given usage
     */
    virtual bool isFormatSupported(
        PixelFormat format,
        BufferUsage usage
    ) const = 0;
    
    /**
     * @brief Get the allocator name for debugging
     */
    virtual const char* getName() const = 0;
};

/**
 * @brief Factory for creating platform-appropriate allocators
 */
class AllocatorFactory {
public:
    /**
     * @brief Create the default allocator for the platform
     */
    static std::unique_ptr<IBufferAllocator> createDefault();
    
    /**
     * @brief Create a specific allocator type
     * @param name Allocator type: "gralloc", "ion", "dmabuf"
     */
    static std::unique_ptr<IBufferAllocator> create(const std::string& name);
};

} // namespace graphics
} // namespace android
