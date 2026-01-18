# IBufferAllocator.h

---

| Property | Value |
|----------|-------|
| **Location** | `include\IBufferAllocator.h` |
| **Lines** | 116 |
| **Classes** | 2 |
| **Functions** | 0 |
| **Last Updated** | 2026-01-18 13:28 |

---

## Quick Navigation

### Classes
- [android::graphics::IBufferAllocator](#android-graphics-ibufferallocator)
- [android::graphics::AllocatorFactory](#android-graphics-allocatorfactory)

---

# Documentation for `IBufferAllocator.h`

## File Context
- **File:** `tests\graphics_buffer_lib\include\IBufferAllocator.h`
- **Lines:** 1 - 116
- **Chunk:** 1 of 1

## Code to Document
```cpp
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

```

## Required Documentation

### 1. Comprehensive Description (2-4 paragraphs)
`IBufferAllocator.h` defines an abstract interface for buffer allocation strategies, providing a core abstraction for different allocation backends such as gralloc, ION, and dmabuf heaps. This interface is essential for managing the lifecycle of graphic buffers in Android applications, ensuring efficient memory management and compatibility across various hardware platforms.

### 2. Parameters (DETAILED for each)
#### `allocate(const BufferDescriptor& descriptor, std::unique_ptr<GraphicBuffer>& outBuffer)`
- **Purpose**: Allocates a new graphic buffer based on the provided `BufferDescriptor`.
- **Type Semantics**: The `descriptor` parameter specifies the geometry and usage requirements of the buffer, while `outBuffer` is a pointer to receive the allocated buffer.
- **Valid Values**: The `descriptor` must contain valid dimensions, pixel format, and usage flags. The `outBuffer` should be a non-null pointer where the allocated buffer will be stored.
- **Ownership**: The `GraphicBuffer` object is owned by the caller after allocation. The `std::unique_ptr` ensures proper memory management.
- **Nullability**: The `outBuffer` parameter can be null, but it must be checked before use to avoid dereferencing a null pointer.

#### `allocateAsync(const BufferDescriptor& descriptor, AllocationCallback callback)`
- **Purpose**: Asynchronously allocates a buffer based on the provided `BufferDescriptor`.
- **Type Semantics**: The `descriptor` parameter specifies the geometry and usage requirements of the buffer, while `callback` is a function that will be called when allocation completes.
- **Valid Values**: The `descriptor` must contain valid dimensions, pixel format, and usage flags. The `callback` should be a non-null pointer to a function that takes an `AllocationStatus` and a `GraphicBuffer*`.
- **Ownership**: The `GraphicBuffer` object is owned by the caller after allocation. The `std::unique_ptr` ensures proper memory management.
- **Nullability**: The `callback` parameter can be null, but it must be checked before use to avoid dereferencing a null pointer.

#### `free(GraphicBuffer* buffer)`
- **Purpose**: Frees a previously allocated buffer.
- **Type Semantics**: The `buffer` parameter is a pointer to the graphic buffer to be freed.
- **Valid Values**: The `buffer` must be a valid, non-null pointer to an allocated buffer.
- **Ownership**: The `GraphicBuffer` object is owned by the caller and should not be deleted after calling this function. The `std::unique_ptr` ensures proper memory management.
- **Nullability**: The `buffer` parameter can be null, but it must be checked before use to avoid dereferencing a null pointer.

#### `importBuffer(const NativeHandle& handle, const BufferDescriptor& descriptor, std::unique_ptr<GraphicBuffer>& outBuffer)`
- **Purpose**: Imports a buffer from an external native handle.
- **Type Semantics**: The `handle` parameter is the external native handle of the buffer to be imported, the `descriptor` specifies the expected properties of the buffer, and `outBuffer` is a pointer to receive the imported buffer.
- **Valid Values**: The `handle` must be a valid, non-null pointer to an external native handle. The `descriptor` must contain valid dimensions, pixel format, and usage flags. The `outBuffer` should be a non-null pointer where the imported buffer will be stored.
- **Ownership**: The `GraphicBuffer` object is owned by the caller after import. The `std::unique_ptr` ensures proper memory management.
- **Nullability**: The `handle`, `descriptor`, and `outBuffer` parameters can be null, but they must be checked before use to avoid dereferencing a null pointer.

#### `getSupportedUsage() const`
- **Purpose**: Retrieves the bitmask of supported BufferUsage flags.
- **Type Semantics**: This function returns a bitmask representing the supported usage flags for the allocator.
- **Valid Values**: The returned bitmask is a combination of valid BufferUsage flags, such as `BUFFER_USAGE_HW_TEXTURE`, `BUFFER_USAGE_VIDEO_ENCODER`, etc.
- **Ownership**: The returned bitmask is owned by the allocator and should not be modified or deleted after use.
- **Nullability**: There are no null values for this function.

#### `isFormatSupported(PixelFormat format, BufferUsage usage) const`
- **Purpose**: Checks if a specific pixel format is supported with given usage flags.
- **Type Semantics**: The `format` parameter specifies the pixel format to check, and the `usage` parameter specifies the usage flags.
- **Valid Values**: The `format` must be a valid PixelFormat value. The `usage` must be a combination of valid BufferUsage flags.
- **Ownership**: There are no null values for this function.
- **Nullability**: There are no null values for this function.

#### `getName() const`
- **Purpose**: Retrieves the name of the allocator for debugging purposes.
- **Type Semantics**: This function returns a constant character pointer representing the name of the allocator.
- **Valid Values**: The returned string is a valid C-style string that represents the allocator's name.
- **Ownership**: The returned string is owned by the allocator and should not be modified or deleted after use.
- **Nullability**: There are no null values for this function.

### 3. Return Value
#### `allocate(const BufferDescriptor& descriptor, std::unique_ptr<GraphicBuffer>& outBuffer)`
- **Purpose**: Allocates a new graphic buffer based on the provided `BufferDescriptor`.
- **Return Value**: Returns an `AllocationStatus` indicating success or failure reason.
- **All Possible Return States**:
  - `ALLOCATION_SUCCESS`: The buffer was successfully allocated and stored in `outBuffer`.
  - `ALLOCATION_ERROR`: An error occurred during allocation, such as insufficient memory or invalid parameters.
- **Error Conditions and How They're Indicated**: If an error occurs, the function returns `ALLOCATION_ERROR` and sets `outBuffer` to a null pointer. The caller should check the return value before using the allocated buffer.
- **Ownership of Returned Objects**: The `GraphicBuffer` object is owned by the caller after allocation. The `std::