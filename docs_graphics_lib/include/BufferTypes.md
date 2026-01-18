# BufferTypes.h

---

| Property | Value |
|----------|-------|
| **Location** | `include\BufferTypes.h` |
| **Lines** | 136 |
| **Classes** | 4 |
| **Functions** | 2 |
| **Last Updated** | 2026-01-18 13:28 |

---

## Quick Navigation

### Classes
- [android::graphics::BufferDescriptor](#android-graphics-bufferdescriptor)
- [android::graphics::NativeHandle](#android-graphics-nativehandle)
- [android::graphics::MappedRegion](#android-graphics-mappedregion)
- [android::graphics::PoolStatistics](#android-graphics-poolstatistics)

### Functions
- [android::graphics::operator|](#android-graphics-operator|)
- [android::graphics::operator&](#android-graphics-operator&)

---

## Documentation for `BufferTypes.h`

### 1. Comprehensive Description (2-4 paragraphs)
The `BufferTypes.h` header file defines fundamental type definitions and structures used throughout the Android Graphics Buffer Management System. These definitions are crucial for managing graphics buffers efficiently, ensuring compatibility with various hardware and software components.

The buffer management system is essential for applications that require high-performance image processing and rendering. It allows developers to allocate and manage memory for graphics buffers, specifying their dimensions, formats, and usage flags. This header file provides a comprehensive set of types and structures to facilitate this process, making it easier to integrate graphics capabilities into Android applications.

### 2. Parameters (DETAILED for each)
#### PixelFormat
- **Purpose**: Defines the pixel format for buffer allocation.
- **Type Semantics**: An enumeration that maps Android HAL pixel formats to their corresponding values.
- **Valid Values**: A set of predefined pixel formats, including common formats like RGBA_8888, RGBX_8888, and YV12.
- **Ownership**: The enum is defined within the `PixelFormat` namespace, so it does not require ownership management.
- **Nullability**: Not applicable; the enum values are fixed.

#### BufferUsage
- **Purpose**: Defines usage flags for buffer allocation. These flags specify how a buffer will be used (e.g., CPU read/write, GPU texture/render target).
- **Type Semantics**: An enumeration that combines multiple flags using bitwise OR operations.
- **Valid Values**: A set of predefined usage flags, including CPU_READ_RARELY, CPU_WRITE_OFTEN, and GPU_TEXTURE.
- **Ownership**: The enum is defined within the `BufferUsage` namespace, so it does not require ownership management.
- **Nullability**: Not applicable; the enum values are fixed.

#### AllocationStatus
- **Purpose**: Defines status codes for buffer allocation operations. These codes indicate whether a buffer was successfully allocated or if an error occurred.
- **Type Semantics**: An enumeration that maps error codes to their corresponding integer values.
- **Valid Values**: A set of predefined error codes, including SUCCESS, ERROR_NO_MEMORY, and ERROR_INVALID_DIMENSIONS.
- **Ownership**: The enum is defined within the `AllocationStatus` namespace, so it does not require ownership management.
- **Nullability**: Not applicable; the enum values are fixed.

#### BufferDescriptor
- **Purpose**: Describes the geometry and format of a buffer. This structure is used to specify the dimensions, stride, pixel format, usage flags, and layer count of a buffer.
- **Type Semantics**: A struct that contains various properties of a buffer.
- **Valid Values**: The `width`, `height`, `stride`, `format`, `usage`, and `layerCount` fields can be set to any valid integer values. The `format` field should match one of the predefined pixel formats, and the `usage` field should combine multiple usage flags using bitwise OR operations.
- **Ownership**: The struct is defined within the `BufferDescriptor` namespace, so it does not require ownership management.
- **Nullability**: Not applicable; all fields are required.

#### NativeHandle
- **Purpose**: Wraps a native handle for gralloc buffers. This structure is used to manage the file descriptor and other properties of a buffer.
- **Type Semantics**: A struct that contains various properties of a buffer's native handle.
- **Valid Values**: The `fd` field should be a valid file descriptor, and the `numFds`, `numInts`, and `data` fields can be set to any integer values. The `data` array is used for additional information about the buffer.
- **Ownership**: The struct is defined within the `NativeHandle` namespace, so it does not require ownership management.
- **Nullability**: Not applicable; all fields are required.

#### MappedRegion
- **Purpose**: Represents a memory region for CPU-side buffer access. This structure is used to map a buffer into memory and provide access to its data.
- **Type Semantics**: A struct that contains various properties of a mapped buffer region.
- **Valid Values**: The `data` field should be a valid pointer, the `size` field should be a non-negative integer value, and the `lockMode` field can be set to any valid lock mode (e.g., 0 for read-only).
- **Ownership**: The struct is defined within the `MappedRegion` namespace, so it does not require ownership management.
- **Nullability**: Not applicable; all fields are required.

#### PoolStatistics
- **Purpose**: Provides statistics for buffer pool monitoring. This structure is used to track various metrics related to a buffer pool.
- **Type Semantics**: A struct that contains various statistics about the buffer pool.
- **Valid Values**: The `totalBuffers`, `freeBuffers`, `allocatedBytes`, `peakAllocatedBytes`, `allocationCount`, and `reuseCount` fields can be set to any non-negative integer values. The `hitRate` field should be a floating-point value between 0.0 and 1.0.
- **Ownership**: The struct is defined within the `PoolStatistics` namespace, so it does not require ownership management.
- **Nullability**: Not applicable; all fields are required.

### 3. Return Value
- **Purpose**: Returns the calculated size of a buffer based on its width, height, stride, and format.
- **Type Semantics**: A size_t value representing the total size of the buffer in bytes.
- **Valid Values**: The returned size is determined by multiplying the `width`, `height`, `stride`, and format-specific byte count.
- **Ownership**: Not applicable; the return value is a simple integer.
- **Nullability**: Not applicable.

### 4. Dependencies Cross-Reference
This header file does not depend on any external classes or functions.

### 5. Side Effects
- State modifications: The `BufferDescriptor` struct modifies its fields based on user input, and the `NativeHandle` struct modifies its fields based on the native buffer's properties.
- Locks acquired/released: None.
- I/O operations: None.
- Signals/events emitted: None.

### 6. Usage Context
This header file is used by various components of the Android Graphics Buffer Management System, including the graphics buffer allocator and pool management modules. It provides a common interface for managing buffers across different parts of the system.

### 7. Related Functions
| Relationship Type | Function Name | Description |
| --- | --- | --- |
| Member Function | `BufferDescriptor::calculateSize()` | Calculates the size of a buffer based on its dimensions and format. |
| Member Function | `BufferDescriptor::isValid()` | Checks if the buffer descriptor is valid. |
| Member Function | `BufferDescriptor::toString()` | Converts the buffer descriptor to a string representation for debugging purposes. |
| Member Function | `NativeHandle::isValid()` | Checks if the native handle is valid. |
| Member Function | `NativeHandle::close()` | Closes the file descriptor associated with the native handle. |
| Member Function | `MappedRegion::isLocked()` | Checks if the mapped region is locked. |

### 8. Code Example
```cpp
#include <buffer_types.h>

int main() {
    // Create a buffer descriptor for an RGBA_8888 buffer with dimensions 1024x768 and usage flags GPU_TEXTURE and CPU_READ_RARELY
    android::graphics::BufferDescriptor desc;
    desc.width = 1024;
    desc.height = 768;
    desc.format = android::graphics::PixelFormat::RGBA_8888;
    desc.usage = android::graphics::BufferUsage::GPU_TEXTURE | android::graphics::BufferUsage::CPU_READ_RARELY;

    // Calculate the size of the buffer
    size_t bufferSize = desc.calculateSize();

    // Allocate a native handle for the buffer
    android::graphics::NativeHandle handle;
    handle.fd = open("/dev/graphics/fb0", O_RDWR);
    if (handle.fd < 0) {
        // Handle error
    }

    // Map the buffer into memory
    android::graphics::MappedRegion region;
    region.data = mmap(nullptr, bufferSize, PROT_READ | PROT_WRITE, MAP_SHARED, handle.fd, 0);
    if (region.data == MAP_FAILED) {
        // Handle error
    }
    region.size = bufferSize;

    // Use the mapped buffer for rendering or processing

    // Unmap and close the buffer
    munmap(region.data, bufferSize);
    close(handle.fd);

    return 0;
}
```

This code example demonstrates how to create a buffer descriptor, calculate its size, allocate a native handle, map the buffer into memory, use it for rendering, and then unmap and close it.