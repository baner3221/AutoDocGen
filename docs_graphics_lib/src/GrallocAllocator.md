# GrallocAllocator.cpp

---

| Property | Value |
|----------|-------|
| **Location** | `src\GrallocAllocator.cpp` |
| **Lines** | 269 |
| **Classes** | 0 |
| **Functions** | 19 |
| **Last Updated** | 2026-01-18 20:54 |

---

## Quick Navigation

### Functions
- [GrallocAllocator::~GrallocAllocator](#grallocallocator-~grallocallocator)
- [GrallocAllocator::allocate](#grallocallocator-allocate)
- [GrallocAllocator::allocateAsync](#grallocallocator-allocateasync)
- [std::thread](#std-thread)
- [GrallocAllocator::free](#grallocallocator-free)
- [GrallocAllocator::importBuffer](#grallocallocator-importbuffer)
- [GrallocAllocator::getSupportedUsage](#grallocallocator-getsupportedusage)
- [GrallocAllocator::isFormatSupported](#grallocallocator-isformatsupported)
- [GrallocAllocator::queryFormatInfo](#grallocallocator-queryformatinfo)
- [GrallocAllocator::dumpState](#grallocallocator-dumpstate)
- [GrallocAllocator::initializeHal](#grallocallocator-initializehal)
- [GrallocAllocator::shutdownHal](#grallocallocator-shutdownhal)
- [GrallocAllocator::allocateInternal](#grallocallocator-allocateinternal)
- [GrallocMapper::~GrallocMapper](#grallocmapper-~grallocmapper)
- [GrallocMapper::lock](#grallocmapper-lock)
- [GrallocMapper::unlock](#grallocmapper-unlock)
- [GrallocMapper::getMetadata](#grallocmapper-getmetadata)
- [AllocatorFactory::createDefault](#allocatorfactory-createdefault)
- [AllocatorFactory::create](#allocatorfactory-create)

---

# GrallocAllocator Documentation

## Overview

The `GrallocAllocator` class is a high-level allocator designed to manage graphics buffers efficiently using the Android Hardware Interface Layer (HAL). It provides automatic HAL version detection, buffer handle caching for performance, and asynchronous allocation support via a thread pool. The allocator supports format negotiation with gralloc and ensures thread safety across all public methods.

## Class Definition

```cpp
namespace android {
namespace graphics {

class GrallocAllocator {
public:
    // Constructor that auto-detects the HAL version
    GrallocAllocator();

    // Constructor allowing explicit specification of the HAL version
    GrallocAllocator(GrallocVersion version);

    // Destructor to clean up resources
    ~GrallocAllocator();
};

}  // namespace graphics
}  // namespace android
```

## Detailed Description

The `GrallocAllocator` class is a central component in managing graphics buffers within the Android system. It leverages the HAL to allocate and manage graphic buffers efficiently, providing features such as automatic HAL version detection, buffer handle caching for performance, and asynchronous allocation support via a thread pool. The allocator supports format negotiation with gralloc and ensures thread safety across all public methods.

## Constructor Details

### GrallocAllocator()

- **Purpose**: Initializes the `GrallocAllocator` instance by auto-detecting the HAL version.
- **Why It Exists**: Automatically selecting the appropriate HAL version is crucial for compatibility and performance, as different versions of the HAL may support different features and optimizations.
- **How It Fits into the Larger Workflow**: This constructor is typically called during the initialization phase of an application or service that requires access to graphics buffers. It ensures that the allocator is configured with the correct HAL version, which can affect how buffers are allocated and managed.

### GrallocAllocator(GrallocVersion version)

- **Purpose**: Initializes the `GrallocAllocator` instance with a specified HAL version.
- **Why It Exists**: Allowing explicit specification of the HAL version allows for more control over resource allocation and performance tuning. This is particularly useful in scenarios where different versions of the HAL may have specific optimizations or features that are beneficial for certain applications.
- **How It Fits into the Larger Workflow**: This constructor is used when the application needs to explicitly configure the allocator with a particular HAL version, such as during runtime configuration changes or when integrating with specific hardware components.

### Destructor

- **Purpose**: Cleans up resources held by the `GrallocAllocator` instance.
- **Why It Exists**: Proper resource management is essential for preventing memory leaks and ensuring that system resources are freed when they are no longer needed. The destructor ensures that all allocated buffers, caches, and other resources are properly released to prevent potential issues in subsequent operations.
- **How It Fits into the Larger Workflow**: This destructor is called at the end of an application's lifecycle or when a `GrallocAllocator` instance is no longer required. It helps maintain system stability and performance by ensuring that all resources are freed before they can be reused.

## Dependencies Cross-Reference

### GrallocMapper

- **Why It's Used**: The `GrallocMapper` class is used to manage the CPU access of a `GraphicBuffer`. It ensures that the buffer is locked when an instance of `BufferLockGuard` is created and unlocked automatically when it goes out of scope.
- **How It's Used in This Context**: The `GrallocAllocator` uses the `GrallocMapper` to handle CPU mapping operations for graphics buffers. This allows applications to directly access the pixel data of a buffer, which is essential for image processing or rendering tasks.

### BufferCache

- **Why It's Used**: The `BufferCache` class is used to cache buffer handles for performance optimization. It stores frequently accessed buffers in memory and reuses them when needed.
- **How It's Used in This Context**: The `GrallocAllocator` uses the `BufferCache` to store and reuse buffer handles, which helps improve allocation efficiency by reducing the overhead of repeatedly allocating and deallocating buffers.

### GrallocVersion

- **Why It's Used**: The `GrallocVersion` enum is used to specify the version of the HAL being used. This allows for compatibility with different versions of the HAL, as each version may support different features and optimizations.
- **How It's Used in This Context**: The `GrallocAllocator` uses the `GrallocVersion` enum to determine which version of the HAL to use when allocating buffers. This ensures that the allocator is configured correctly for the specific hardware and software environment.

## Side Effects

### State Modifications

- **State Modifications**: The `GrallocAllocator` modifies its internal state, including the HAL version, buffer cache, and thread pool configuration.
- **Locks Acquired/Released**: The `GrallocAllocator` acquires locks during initialization and release resources during destruction.
- **I/O Operations**: The `GrallocAllocator` performs I/O operations to communicate with the HAL for buffer allocation and management.

### Signals/Events Emitted

- **Signals/Events Emitted**: The `GrallocAllocator` emits signals or events related to buffer allocation, deallocation, and cache management.
- **Usage Context**: These signals/events are typically used by other components within the Android system to synchronize with the allocator's operations.

## Usage Context

The `GrallocAllocator` is called during the initialization phase of an application or service that requires access to graphics buffers. It is typically used in scenarios where direct access to hardware-accelerated resources is necessary, such as image processing or rendering tasks.

### Prerequisites

- **Prerequisites**: The application must have access to the HAL and be configured to use the `GrallocAllocator`.
- **Usage Context**: This class is used by various components within the Android system that require access to graphics buffer management functionalities.

## Related Functions

| Relationship Type | Function Name | Description |
|------------------|--------------|-------------|
| Constructor       | GrallocAllocator() | Initializes the `GrallocAllocator` instance by auto-detecting the HAL version. |
| Constructor       | GrallocAllocator(GrallocVersion version) | Initializes the `GrallocAllocator` instance with a specified HAL version. |
| Destructor        | ~GrallocAllocator() | Cleans up resources held by the `GrallocAllocator` instance. |

## Code Example

```cpp
#include <android/graphics/GrallocAllocator.h>

int main() {
    // Initialize the GrallocAllocator
    android::graphics::GrallocAllocator allocator;

    // Allocate a new graphics buffer
    android::sp<GraphicBuffer> buffer = allocator.allocate(1024, 768, HAL_PIXEL_FORMAT_RGBA_8888);

    // Use the allocated buffer for rendering or image processing

    // Deallocate the buffer when no longer needed
    buffer.clear();

    return 0;
}
```

In this example, the `GrallocAllocator` is initialized and used to allocate a new graphics buffer. The buffer is then used for rendering or image processing tasks, and finally deallocated when it is no longer required. This demonstrates how the `GrallocAllocator` can be integrated into an application that requires access to hardware-accelerated resources.

## Documentation for `GrallocAllocator::allocate`

### 1. Comprehensive Description (2-4 paragraphs)
The `allocate` function is a core method of the `GrallocAllocator` class, responsible for allocating a new graphics buffer based on the provided `BufferDescriptor`. This function ensures that the requested buffer meets certain criteria, such as valid dimensions and supported formats, before proceeding with the allocation. The allocator uses thread-safe mechanisms to manage buffer allocations and handles caching to optimize performance.

### 2. Parameters (DETAILED for each)
- **descriptor**: A `BufferDescriptor` object containing details about the desired buffer, including its format and usage flags.
  - **Purpose**: Specifies the characteristics of the buffer to be allocated.
  - **Type Semantics**: Represents a descriptor that defines the properties of the buffer, such as width, height, pixel format, and usage flags.
  - **Valid Values**: The dimensions must be within valid limits (e.g., non-negative integers). The pixel format must be supported by the HAL. Usage flags can include CPU read/write operations or GPU rendering targets.
  - **Ownership**: The caller owns the `BufferDescriptor` object and is responsible for its lifecycle.
  - **Nullability**: Cannot be null.

- **outBuffer**: A reference to a `std::unique_ptr<GraphicBuffer>` that will hold the newly allocated buffer once it is successfully created.
  - **Purpose**: Provides a way to return the allocated buffer back to the caller.
  - **Type Semantics**: A smart pointer that manages the lifetime of the `GraphicBuffer` object, ensuring proper memory management.
  - **Valid Values**: The reference must be valid and point to a location where the allocator can store the newly created buffer.
  - **Ownership**: The allocator transfers ownership of the allocated buffer to the caller through this reference.
  - **Nullability**: Can be null if the allocation fails.

### 3. Return Value
- **AllocationStatus**: An enumeration representing the result of the allocation process, indicating whether the operation was successful or an error occurred.
  - **Purpose**: Provides feedback on the outcome of the buffer allocation attempt.
  - **Type Semantics**: A status code that indicates success or failure, along with any specific error details.
  - **Valid Values**: Possible values include `AllocationStatus::SUCCESS`, `AllocationStatus::ERROR_INVALID_DIMENSIONS`, and `AllocationStatus::ERROR_UNSUPPORTED_FORMAT`.
  - **Ownership**: The allocator does not transfer ownership of the return value; it is returned as a status code.
  - **Nullability**: Not applicable.

### 4. Dependencies Cross-Reference
- **BufferDescriptor**: [BufferDescriptor](#bufferdescriptor)
- **GraphicBuffer**: [GraphicBuffer](#graphicbuffer)
- **NativeHandle**: [NativeHandle](#nativehandle)
- **AllocationStatus**: [AllocationStatus](#allocationstatus)

### 5. Side Effects
- **State Modifications**: The allocator modifies its internal state by adding the newly allocated buffer to the `activeBuffers_` map and caching it in the `cache_`.
- **Locks Acquired/Released**: The function acquires a lock (`allocMutex_`) to ensure thread safety during allocation.
- **I/O Operations**: No I/O operations are performed within this function.
- **Signals/Events Emitted**: No signals or events are emitted by this function.

### 6. Usage Context
This function is typically called when an application needs to allocate a new graphics buffer for rendering, video processing, or other graphical tasks. It is used in various parts of the Android system, such as SurfaceFlinger and AudioFlinger, where efficient buffer management is crucial.

### 7. Related Functions
| Relationship Type | Function Name | Description |
| --- | --- | --- |
| Calls | `allocateInternal` | Performs the actual allocation logic using the HAL. |
| Uses | `BufferCacheEntry` | Stores information about cached buffers for future use. |

### 8. Code Example

```cpp
// Example usage of GrallocAllocator::allocate
GrallocAllocator allocator;
BufferDescriptor descriptor(/* specify buffer dimensions and format */);
std::unique_ptr<GraphicBuffer> buffer;

AllocationStatus status = allocator.allocate(descriptor, buffer);

if (status == AllocationStatus::SUCCESS) {
    // Buffer allocation was successful
    // Use the allocated buffer for rendering or processing
} else {
    // Handle error
}
```

This example demonstrates how to use the `GrallocAllocator` class to allocate a new graphics buffer and handle its allocation status.

## Documentation for `GrallocAllocator::free`

### 1. Comprehensive Description (2-4 paragraphs)
The `free` function is a crucial method in the `GrallocAllocator` class, responsible for releasing a previously allocated `GraphicBuffer`. This function ensures that the buffer is properly cleaned up and returned to the system resources, freeing up memory and preventing resource leaks.

When a `GraphicBuffer` is no longer needed, it must be released to free up its associated resources. The `free` function performs several key actions to achieve this:

1. **Validation**: It first checks if the provided `GraphicBuffer` pointer is valid. If not, it returns immediately without performing any further operations.

2. **Mutex Locking**: The function acquires a mutex lock (`allocMutex_`) to ensure thread safety when accessing shared resources such as the active buffers and cache.

3. **ID Retrieval**: It retrieves the buffer's unique identifier (`id`) using `buffer->getBufferId()`. This ID is used to identify the specific buffer in the allocator's internal data structures.

4. **Active Buffer Removal**: The function removes the buffer from the list of active buffers (`activeBuffers_`). This step ensures that the buffer is no longer considered active and can be safely released.

5. **Cache Invalidation**: It invalidates the cache entry for the buffer using `cache_->invalidate(id)`. This helps in managing memory efficiently by ensuring that any cached references to the buffer are updated or removed.

6. **Platform-Specific Free**: The function would typically call a platform-specific function (`gralloc->freeBuffer(buffer->getNativeHandle())`) to release the underlying native handle of the buffer. This step ensures that all system resources associated with the buffer are freed.

7. **Release Resources**: After releasing the buffer, it is important to ensure that any references or locks held by other parts of the system are properly released to avoid memory leaks or undefined behavior.

### 2. Parameters (DETAILED for each)
- **Purpose**: Why does this parameter exist?
- **Type Semantics**: What does the type represent?
- **Valid Values**: Acceptable range, constraints
- **Ownership**: Who owns memory? Borrowed or transferred?
- **Nullability**: Can it be null? What happens?

The `free` function takes a single parameter:

- **buffer** (`GraphicBuffer*`)
  - **Purpose**: A pointer to the `GraphicBuffer` that needs to be released.
  - **Type Semantics**: This is a raw pointer to an instance of the `GraphicBuffer` class. It represents the buffer whose resources are to be freed.
  - **Valid Values**: The function expects a valid, non-null pointer to a `GraphicBuffer`.
  - **Ownership**: The caller owns the `GraphicBuffer` and must ensure that it is not used after calling `free`. If the buffer is no longer needed, it should be deleted or reset.
  - **Nullability**: The parameter can be null. If it is null, the function will return immediately without performing any operations.

### 3. Return Value
- What does it represent?
- All possible return states
- Error conditions and how they're indicated
- Ownership of returned objects

The `free` function does not have a return value. It returns void, indicating that no data is returned to the caller.

### 4. Dependencies Cross-Reference
For each external class/function used:
- **ClassName::method()**
  - **Purpose**: Why it's used in this context?
  - **How it's used**: The function uses a mutex lock (`allocMutex_`) from the `std::mutex` library to ensure thread safety when accessing shared resources.
  - **Link format**: [std::mutex::lock](https://en.cppreference.com/w/cpp/thread/mutex/lock)

### 5. Side Effects
- State modifications:
  - The function modifies the state of the allocator by removing the buffer from the list of active buffers and invalidating its cache entry.
  - It releases system resources associated with the buffer, including the native handle (`gralloc->freeBuffer(buffer->getNativeHandle())`).
- Locks acquired/released:
  - The function acquires a mutex lock (`allocMutex_`) to ensure thread safety when accessing shared resources.
  - The lock is released automatically when the `std::lock_guard<std::mutex>` object goes out of scope.
- I/O operations:
  - The function performs platform-specific I/O operations to release the native handle of the buffer.
- Signals/events emitted: None

### 6. Usage Context
The `free` function is typically called in scenarios where a `GraphicBuffer` is no longer needed, such as when rendering or video processing tasks are complete. It should be used by any component that manages graphics buffers to ensure proper resource management and avoid memory leaks.

### 7. Related Functions
| Relationship Type | Function Name | Description |
|------------------|--------------|-------------|
| Calls            | `freeBuffer`   | Platform-specific function to release the native handle of a buffer. |

### 8. Code Example

```cpp
// Example usage of GrallocAllocator::free
GrallocAllocator allocator;
GraphicBuffer* buffer = allocator.allocate(/* parameters */);

// Use the buffer...

allocator.free(buffer); // Release the buffer when it is no longer needed
```

This code snippet demonstrates how to allocate a `GraphicBuffer` using an instance of `GrallocAllocator`, use it for rendering or video processing, and then release it when it is no longer required. The `free` function ensures that all resources associated with the buffer are properly released, freeing up memory and preventing resource leaks.

## Documentation for `GrallocAllocator::importBuffer`

### 1. Comprehensive Description (2-4 paragraphs)
The `importBuffer` function is a crucial method in the Android graphics buffer library, designed to import an existing native handle into a `GraphicBuffer`. This function is essential for applications that need to work with pre-existing graphics buffers or those acquired from other sources, such as camera captures or video decoding. The function ensures that the imported buffer is properly managed and can be used by the application without further allocation.

The primary purpose of this function is to facilitate seamless integration between different components within the Android system, allowing for efficient data sharing and processing. By importing a buffer, applications can avoid unnecessary memory allocations and improve performance by reusing existing resources.

This function fits into the larger workflow by providing a way to integrate external graphics buffers into the application's rendering pipeline. It is particularly useful in scenarios where the application needs to process or display images captured from a camera or received from a video decoder.

The `importBuffer` function uses the Android Hardware Interface Layer (HAL) to manage the buffer, ensuring that it can be accessed and used efficiently by different system components. The function supports various buffer usages, such as CPU read/write operations, GPU texture rendering, and camera input/output, making it versatile for a wide range of applications.

### 2. Parameters (DETAILED for each)
- **handle**: A `NativeHandle` object representing the handle to the graphics buffer.
  - **Purpose**: This parameter provides the native handle that points to the existing graphics buffer.
  - **Type Semantics**: The `NativeHandle` type represents a platform-specific handle used to identify and manage resources in Android.
  - **Valid Values**: The handle must be valid and point to an existing graphics buffer. It is expected to be registered with the HAL before being passed to this function.
  - **Ownership**: The caller owns the memory pointed to by `handle`. The function does not take ownership of the handle; it only uses it to create a new `GraphicBuffer`.
  - **Nullability**: This parameter cannot be null. If `handle` is invalid, the function will return an error status.

- **descriptor**: A `BufferDescriptor` object specifying the dimensions and properties of the buffer.
  - **Purpose**: This parameter provides the descriptor that defines the size, format, and other attributes of the graphics buffer.
  - **Type Semantics**: The `BufferDescriptor` type represents a description of the buffer's characteristics.
  - **Valid Values**: The descriptor must be valid and contain all necessary information about the buffer. It specifies parameters such as width, height, pixel format, usage flags, and other relevant properties.
  - **Ownership**: The caller owns the memory pointed to by `descriptor`. The function does not take ownership of the descriptor; it only uses it to create a new `GraphicBuffer`.
  - **Nullability**: This parameter cannot be null. If `descriptor` is invalid, the function will return an error status.

- **outBuffer**: A pointer to a `std::unique_ptr<GraphicBuffer>` that will hold the newly created `GraphicBuffer` object.
  - **Purpose**: This parameter is used to store the result of the import operation. The function creates a new `GraphicBuffer` object and assigns it to this pointer.
  - **Type Semantics**: The `std::unique_ptr<GraphicBuffer>` type represents a smart pointer that manages the lifetime of a `GraphicBuffer`.
  - **Valid Values**: The `outBuffer` parameter must be a valid pointer to a `std::unique_ptr<GraphicBuffer>`. It is expected to point to an uninitialized `std::unique_ptr<GraphicBuffer>`.
  - **Ownership**: The function transfers ownership of the newly created `GraphicBuffer` object to the caller. After the function returns, the caller is responsible for managing the lifetime of the `GraphicBuffer`.
  - **Nullability**: This parameter cannot be null. If `outBuffer` is invalid, the function will return an error status.

### 3. Return Value
- The function returns a `AllocationStatus` enum value indicating the success or failure of the import operation.
  - **Purpose**: This return value provides feedback on whether the buffer was successfully imported and can be used by the caller.
  - **Type Semantics**: The `AllocationStatus` type is an enumeration that represents different possible outcomes of the import operation.
  - **Valid Values**: The valid values are:
    - `AllocationStatus::SUCCESS`: Indicates that the buffer was successfully imported and can be used by the application.
    - `AllocationStatus::ERROR_GRALLOC_FAILURE`: Indicates that there was a failure during the import process, likely due to an error in the HAL or other system components.
  - **Ownership**: The return value is not owned by the function; it is returned as part of the function's output.
  - **Nullability**: This return value cannot be null.

### 4. Dependencies Cross-Reference
- **NativeHandle**: Represents a platform-specific handle used to identify and manage resources in Android.
  - **Why It's Used**: The `NativeHandle` is used to provide access to the existing graphics buffer that needs to be imported.
  - **How It's Used**: The function uses the `NativeHandle` to create a new `GraphicBuffer` object. It does not take ownership of the handle; it only uses it to identify and manage the existing buffer.

- **BufferDescriptor**: Represents a description of the buffer's characteristics.
  - **Why It's Used**: The `BufferDescriptor` is used to specify the dimensions, format, and other properties of the graphics buffer that needs to be imported.
  - **How It's Used**: The function uses the `BufferDescriptor` to create a new `GraphicBuffer` object. It does not take ownership of the descriptor; it only uses it to define the characteristics of the buffer.

- **GraphicBuffer**: Represents an allocated graphics buffer in Android, providing functionalities such as CPU mapping, GPU resource binding, reference counting, and fence synchronization.
  - **Why It's Used**: The `GraphicBuffer` is used to store the newly created buffer object that was imported from the native handle.
  - **How It's Used**: The function creates a new `GraphicBuffer` object using the provided descriptor and native handle. It then stores this object in the `activeBuffers_` map, which keeps track of all active buffers managed by the allocator.

### 5. Side Effects
- This function acquires a lock on the `allocMutex_` mutex to ensure thread safety when importing the buffer.
- The function creates a new `GraphicBuffer` object using the provided descriptor and native handle.
- It stores this newly created `GraphicBuffer` object in the `activeBuffers_` map, which keeps track of all active buffers managed by the allocator.
- The function releases the lock on the `allocMutex_` mutex after completing the import operation.

### 6. Usage Context
This function is typically called when an application needs to work with a pre-existing graphics buffer or one acquired from another source, such as camera captures or video decoding. It is used in scenarios where the application needs to integrate existing resources into its rendering pipeline without unnecessary memory allocations.

The typical callers of this function are components within the Android system that require access to graphics buffer management functionalities. These components may include the SurfaceFlinger, AudioFlinger, and other system services that need to process or display images captured from a camera or received from a video decoder.

### 7. Related Functions
| Relationship Type | Function Name | Description |
|------------------|--------------|-------------|
| Dependency        | `BufferDescriptor` | Provides the dimensions and properties of the buffer. |
| Dependency        | `GraphicBuffer` | Represents an allocated graphics buffer in Android, providing functionalities such as CPU mapping, GPU resource binding, reference counting, and fence synchronization. |

### 8. Code Example
```cpp
NativeHandle handle = ...; // Obtain a valid NativeHandle from somewhere
BufferDescriptor descriptor = ...; // Obtain a valid BufferDescriptor

std::unique_ptr<GraphicBuffer> outBuffer;
AllocationStatus status = GrallocAllocator::importBuffer(handle, descriptor, outBuffer);

if (status == AllocationStatus::SUCCESS) {
    // Use the imported buffer for rendering or processing
} else {
    // Handle the error
}
```

This code example demonstrates how to use the `importBuffer` function to import a graphics buffer from a native handle and store it in a `std::unique_ptr<GraphicBuffer>`. The function is called with valid `NativeHandle` and `BufferDescriptor` objects, and the result is checked for success or failure. If successful, the imported buffer can be used by the application for rendering or processing tasks.

## Documentation for `GrallocAllocator::isFormatSupported`

### 1. Comprehensive Description (2-4 paragraphs)
The `isFormatSupported` function checks if a given pixel format and buffer usage combination is supported by the Gralloc allocator. This function is crucial for applications that need to ensure compatibility with different hardware configurations and rendering requirements.

Gralloc, the Android Hardware Interface Layer's graphics buffer manager, supports various pixel formats and buffer usages. The `isFormatSupported` function provides a simple way to determine if a specific format and usage combination can be used without encountering issues during allocation or usage.

### 2. Parameters (DETAILED for each)
- **format**: PixelFormat
  - **Purpose**: Specifies the desired pixel format of the buffer.
  - **Type Semantics**: Represents an enumeration value from `BufferTypes.h` that maps Android HAL pixel formats to a more readable format.
  - **Valid Values**: A set of predefined pixel formats such as RGBA_8888, RGBX_8888, etc. These values are defined in the `BufferTypes.h` file and represent different color spaces and bit depths.
  - **Ownership**: The caller owns the memory for this parameter.
  - **Nullability**: This parameter cannot be null.

- **usage**: BufferUsage
  - **Purpose**: Specifies the intended usage of the buffer, such as CPU read/write operations or GPU rendering targets.
  - **Type Semantics**: Represents an enumeration value from `BufferTypes.h` that defines flags for buffer usage. These flags can be combined using bitwise OR to specify multiple usage scenarios.
  - **Valid Values**: A set of predefined buffer usage flags such as USAGE_CPU_READ, USAGE_GPU_RENDER_TARGET, etc. These values are defined in the `BufferTypes.h` file and represent different access patterns and rendering requirements.
  - **Ownership**: The caller owns the memory for this parameter.
  - **Nullability**: This parameter cannot be null.

### 3. Return Value
- **Type**: bool
  - **Purpose**: Indicates whether the specified pixel format and usage combination is supported by Gralloc.
  - **All Possible Return States**:
    - `true`: The format and usage combination is supported.
    - `false`: The format and usage combination is not supported.
  - **Error Conditions and How They're Indicated**: None.
  - **Ownership of Returned Objects**: No objects are returned.

### 4. Dependencies Cross-Reference
- [BufferTypes.h](#buffertypesh)
  - Used to define pixel formats and buffer usage flags.
- [GrallocAllocator::initializeHal()](#grallocallocatorinitializehal)
  - Called to initialize the Gralloc allocator, which is necessary for querying format support.

### 5. Side Effects
- **State Modifications**: None.
- **Locks Acquired/Released**: No locks are acquired or released.
- **I/O Operations**: None.
- **Signals/Events Emitted**: None.

### 6. Usage Context
The `isFormatSupported` function is typically called during the initialization phase of an application, before attempting to allocate a buffer with the specified format and usage combination. This ensures that the application can handle unsupported formats gracefully without crashing or encountering unexpected behavior.

### 7. Related Functions
| Relationship Type | Function Name | Description |
|------------------|--------------|-------------|
| Calls            | GrallocAllocator::queryFormatInfo | Used to query additional information about a format, such as stride. |

### 8. Code Example

```cpp
// Example usage of isFormatSupported function
PixelFormat format = PixelFormat::RGBA_8888;
BufferUsage usage = USAGE_CPU_READ | USAGE_GPU_RENDER_TARGET;

if (GrallocAllocator::isFormatSupported(format, usage)) {
    std::cout << "The specified format and usage combination is supported." << std::endl;
} else {
    std::cout << "The specified format and usage combination is not supported." << std::endl;
}
```

This example demonstrates how to use the `isFormatSupported` function to check if a specific pixel format and buffer usage combination is supported by the Gralloc allocator.

## Documentation for `GrallocAllocator::allocateInternal`

### 1. Comprehensive Description (2-4 paragraphs)
The `allocateInternal` function is a crucial method within the `GrallocAllocator` class, responsible for allocating a new graphics buffer based on the provided `BufferDescriptor`. This function leverages the Android Hardware Interface Layer (HAL) to manage the allocation process efficiently. It simulates the actual HAL call by setting up a mock `NativeHandle` with placeholder values and dimensions.

### 2. Parameters (DETAILED for each)
- **descriptor**: A `BufferDescriptor` object that specifies the desired properties of the buffer, such as width, height, format, and usage flags.
  - **Purpose**: Defines the characteristics of the buffer to be allocated.
  - **Type Semantics**: Represents a descriptor structure containing buffer dimensions, pixel format, and usage hints.
  - **Valid Values**: The `BufferDescriptor` should contain valid dimensions (positive integers) and supported pixel formats. Usage flags can include CPU read/write operations or GPU rendering targets.
  - **Ownership**: Passed by value.
  - **Nullability**: Not null.

- **outHandle**: A reference to a `NativeHandle` object that will be populated with the allocated buffer's handle information.
  - **Purpose**: Provides the output for the allocated buffer's metadata, such as file descriptor, number of FDs, and dimensions.
  - **Type Semantics**: Represents a native handle structure containing various attributes of the allocated buffer.
  - **Valid Values**: The `NativeHandle` should be initialized with appropriate values after allocation.
  - **Ownership**: Passed by reference. The function will modify this object to store the allocated buffer's details.
  - **Nullability**: Not null.

### 3. Return Value
- **AllocationStatus::SUCCESS**: Indicates that the buffer was successfully allocated and populated with the provided `NativeHandle`.
  - **Purpose**: Returns a status indicating the outcome of the allocation process.
  - **Type Semantics**: An enumeration representing the result of the allocation operation.
  - **Valid Values**: Only one valid value, SUCCESS.
  - **Ownership**: Not applicable.
  - **Nullability**: Not null.

### 4. Dependencies Cross-Reference
- **GrallocVersion**: The version of the Gralloc HAL being used for allocation.
  - **Why it's used**: Determines which version-specific methods to call within the HAL.
  - **How it's used in this context**: Passed as a constructor argument to initialize the `GrallocMapper` instance.

- **NativeHandle**: A structure representing a native handle, typically used for passing buffer metadata and file descriptors between system components.
  - **Why it's used**: Provides a way to store and manage buffer-related information.
  - **How it's used in this context**: Modified by the function to include allocated buffer details.

- **BufferDescriptor**: A structure defining the properties of the buffer to be allocated, including dimensions, format, and usage flags.
  - **Why it's used**: Specifies the requirements for the allocated buffer.
  - **How it's used in this context**: Passed as an argument to determine the buffer's characteristics.

### 5. Side Effects
- **State Modifications**:
  - The `NativeHandle` object is populated with the allocated buffer's details, including file descriptor, number of FDs, and dimensions.
  - The `GrallocMapper` instance may be initialized or updated based on the Gralloc version.

- **Locks Acquired/Released**: No locks are acquired or released within this function.

- **I/O Operations**:
  - Simulated I/O operations to set up a mock `NativeHandle`.
  - No actual I/O is performed in this simulation.

- **Signals/Events Emitted**: No signals or events are emitted by this function.

### 6. Usage Context
This function is typically called when an application needs to allocate a new graphics buffer for rendering, video processing, or other graphical operations. It is used within the larger workflow of managing graphics resources in Android applications.

### 7. Related Functions
| Relationship Type | Function Name | Description |
|------------------|--------------|-------------|
| Calls            | GrallocMapper::lock | Locks a buffer for CPU access. |
| Calls            | GrallocMapper::unlock | Unlocks a buffer after CPU access. |

### 8. Code Example

```cpp
// Example usage of allocateInternal
BufferDescriptor descriptor;
descriptor.width = 1920;
descriptor.height = 1080;
descriptor.format = HAL_PIXEL_FORMAT_RGBA_8888;
descriptor.usage = GRALLOC_USAGE_HW_TEXTURE | GRALLOC_USAGE_SW_READ_OFTEN;

NativeHandle handle;
AllocationStatus status = GrallocAllocator::allocateInternal(descriptor, handle);

if (status == AllocationStatus::SUCCESS) {
    // Buffer allocated successfully
    int width = static_cast<int>(handle.data[0]);
    int height = static_cast<int>(handle.data[1]);
    int format = static_cast<PixelFormat>(handle.data[2]);

    // Use the buffer for rendering or processing
} else {
    // Handle allocation failure
}
```

This code snippet demonstrates how to use the `allocateInternal` function to allocate a new graphics buffer with specific dimensions and pixel format, and then retrieve its width, height, and format.

## Documentation for `AllocatorFactory::createDefault` and `AllocatorFactory::create`

### 1. Comprehensive Description (2-4 paragraphs)

The `AllocatorFactory` class provides a factory mechanism to create instances of `IBufferAllocator`, which is responsible for managing the allocation and management of graphic buffers in Android applications. The `createDefault` function creates an instance of `GrallocAllocator`, which is a high-level allocator that leverages the Android Hardware Interface Layer (HAL) to manage graphics buffers efficiently.

The `create` function allows developers to specify the type of buffer allocator they want to create based on the provided name. It supports different versions of the gralloc HAL, allowing for compatibility with various hardware configurations and requirements. If no specific name is provided, it defaults to creating a GrallocAllocator instance using the latest version available.

### 2. Parameters (DETAILED for each)

#### `name` (const std::string&)

- **Purpose**: Specifies the type of buffer allocator to create.
- **Type Semantics**: A string that represents the name of the allocator, such as "gralloc", "gralloc4", "gralloc3", or "gralloc2".
- **Valid Values**: Accepts any valid string representing a gralloc HAL version. The function supports versions 2.0, 3.0, and 4.0.
- **Ownership**: The caller owns the memory of the `name` parameter.
- **Nullability**: Can be null, but if it is, the function will default to creating a GrallocAllocator instance using the latest version available.

### 3. Return Value

- **Representation**: Returns a unique pointer to an `IBufferAllocator` object.
- **All Possible Return States**:
  - A valid `GrallocAllocator` instance created based on the specified name or the default if no specific name is provided.
- **Error Conditions and How They're Indicated**: If the provided name does not match any supported gralloc HAL version, the function will return a null pointer. This can be checked by verifying that the returned `std::unique_ptr` is not empty.
- **Ownership of Returned Objects**: The caller owns the returned `IBufferAllocator` object.

### 4. Dependencies Cross-Reference

- **GrallocAllocator**: Used to create instances of `IBufferAllocator`.
- **GrallocVersion**: Enum used to specify different versions of the gralloc HAL.

### 5. Side Effects

- State Modifications: The function modifies the internal state of the `AllocatorFactory` class by creating a new instance of `GrallocAllocator`.
- Locks Acquired/Released: No locks are acquired or released during this operation.
- I/O Operations: No I/O operations are performed.
- Signals/Events Emitted: No signals or events are emitted.

### 6. Usage Context

- **When is this called?**: This function is typically called when a new `IBufferAllocator` instance is needed for managing graphic buffers in an Android application.
- **Prerequisites**: The caller must have access to the `AllocatorFactory` class and be able to handle the returned `std::unique_ptr`.
- **Typical Callers**: Developers, system components like SurfaceFlinger or AudioFlinger, and other applications that require efficient buffer management.

### 7. Related Functions

| Relationship Type | Function Name | Description |
|------------------|--------------|-------------|
| Implementation of | createDefault | Creates a default GrallocAllocator instance. |
| Implementation of | create | Allows creation of a GrallocAllocator based on the specified name. |

### 8. Code Example

```cpp
// Create a default GrallocAllocator instance
std::unique_ptr<IBufferAllocator> allocator = AllocatorFactory::createDefault();

// Check if the allocation was successful
if (allocator) {
    // Use the allocator to manage graphic buffers
} else {
    // Handle the error case where the allocator could not be created
}
```

This code example demonstrates how to use the `AllocatorFactory` class to create a default GrallocAllocator instance and check for success before using it.

<!-- validation_failed: missing [~GrallocAllocator, allocateAsync, thread, getSupportedUsage, queryFormatInfo, dumpState, initializeHal, shutdownHal, ~GrallocMapper, lock, unlock, getMetadata] -->