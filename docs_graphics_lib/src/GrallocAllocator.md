# GrallocAllocator.cpp

---

| Property | Value |
|----------|-------|
| **Location** | `src\GrallocAllocator.cpp` |
| **Lines** | 269 |
| **Classes** | 0 |
| **Functions** | 0 |
| **Last Updated** | 2026-01-18 13:28 |

---

## Documentation for `GrallocAllocator`

### 1. Comprehensive Description (2-4 paragraphs)
The `GrallocAllocator` class is a crucial component of the Android graphics system, responsible for managing and allocating memory buffers used by various graphics operations. It provides an interface to allocate, import, and manage graphic buffers using the HAL (Hardware Abstraction Layer) provided by the Android platform. The allocator supports different buffer formats and usage flags, ensuring compatibility with various hardware accelerators and rendering pipelines.

The `GrallocAllocator` class is designed to be thread-safe, allowing concurrent allocation requests while maintaining integrity of the internal state. It uses a cache mechanism to store recently allocated buffers for quick retrieval, reducing the overhead of repeated allocations.

### 2. Parameters (DETAILED for each)
#### allocate
- **Purpose**: Allocates a new graphic buffer based on the provided descriptor and usage flags.
- **Type Semantics**: `const BufferDescriptor&` represents the dimensions and format of the buffer to be allocated, while `std::unique_ptr<GraphicBuffer>& outBuffer` is a pointer to the newly created buffer object.
- **Valid Values**: The buffer descriptor must have valid width and height values, and the format must be supported by the allocator. Usage flags should be compatible with the requested format.
- **Ownership**: The buffer handle is transferred from the HAL to the allocator, which then manages its lifecycle. The `outBuffer` pointer is set to point to a new `GraphicBuffer` object created using the allocated handle and descriptor.
- **Nullability**: The `outBuffer` parameter can be null if the allocation fails.

#### allocateAsync
- **Purpose**: Allocates a graphic buffer asynchronously, launching a separate thread for the allocation process.
- **Type Semantics**: `const BufferDescriptor&` represents the dimensions and format of the buffer to be allocated, while `AllocationCallback callback` is a function pointer that will be called with the result of the allocation.
- **Valid Values**: The buffer descriptor must have valid width and height values, and the format must be supported by the allocator. Usage flags should be compatible with the requested format.
- **Ownership**: The buffer handle is transferred from the HAL to the allocator, which then manages its lifecycle. The `callback` function will be called on a separate thread.
- **Nullability**: The `callback` parameter can be null if the allocation fails.

#### free
- **Purpose**: Frees an allocated graphic buffer and removes it from the active list and cache.
- **Type Semantics**: `GraphicBuffer*` is a pointer to the buffer to be freed. If the buffer is null, the function does nothing.
- **Valid Values**: The buffer must have been previously allocated using the allocator.
- **Ownership**: The buffer handle is released back to the HAL, and the `GraphicBuffer` object is destroyed.
- **Nullability**: The `buffer` parameter can be null.

#### importBuffer
- **Purpose**: Imports an existing graphic buffer from a native handle and adds it to the active list and cache.
- **Type Semantics**: `const NativeHandle&` represents the native handle of the buffer to be imported, while `const BufferDescriptor&` represents the dimensions and format of the buffer. `std::unique_ptr<GraphicBuffer>& outBuffer` is a pointer to the newly created buffer object.
- **Valid Values**: The native handle must be valid and represent an existing graphic buffer. The buffer descriptor must have valid width and height values, and the format must match the imported buffer.
- **Ownership**: The buffer handle is transferred from the HAL to the allocator, which then manages its lifecycle. The `outBuffer` pointer is set to point to a new `GraphicBuffer` object created using the imported handle and descriptor.
- **Nullability**: The `outBuffer` parameter can be null if the import fails.

#### getSupportedUsage
- **Purpose**: Returns a bitmask of supported buffer usage flags.
- **Type Semantics**: `BufferUsage` is an enumeration representing various usage flags for graphic buffers. This function returns a bitmask that includes all supported usage flags.
- **Valid Values**: The returned bitmask will include flags such as CPU_READ_OFTEN, CPU_WRITE_OFTEN, GPU_TEXTURE, GPU_RENDER_TARGET, CAMERA_INPUT, CAMERA_OUTPUT, VIDEO_ENCODER, VIDEO_DECODER, and COMPOSER_OVERLAY.
- **Ownership**: No ownership is transferred.
- **Nullability**: No nullability.

#### isFormatSupported
- **Purpose**: Checks if a specific format is supported for the given usage flags.
- **Type Semantics**: `PixelFormat` represents the pixel format to be checked, while `BufferUsage` represents the usage flags. The function returns a boolean indicating whether the format is supported.
- **Valid Values**: The format must be one of the supported formats (e.g., RGBA_8888, RGBX_8888, etc.). Usage flags should be compatible with the requested format.
- **Ownership**: No ownership is transferred.
- **Nullability**: No nullability.

#### queryFormatInfo
- **Purpose**: Queries information about a specific format and usage flags, such as the recommended stride for the buffer.
- **Type Semantics**: `PixelFormat` represents the pixel format to be queried, while `BufferUsage` represents the usage flags. `uint32_t& outStride` is a reference to an integer that will store the recommended stride value.
- **Valid Values**: The format must be one of the supported formats (e.g., RGBA_8888, RGBX_8888, etc.). Usage flags should be compatible with the requested format. The `outStride` parameter will be set to a non-zero value if the query is successful.
- **Ownership**: No ownership is transferred.
- **Nullability**: The `outStride` parameter can be null.

#### dumpState
- **Purpose**: Dumps the current state of the allocator, including active buffer counts and cache hit rates.
- **Type Semantics**: No parameters are required. The function returns a string containing the allocator's state information.
- **Valid Values**: The returned string will contain details about the allocator's internal state.
- **Ownership**: No ownership is transferred.
- **Nullability**: No nullability.

#### initializeHal
- **Purpose**: Initializes the HAL interface for the allocator.
- **Type Semantics**: No parameters are required. The function returns a boolean indicating whether initialization was successful.
- **Valid Values**: The returned boolean will be true if the HAL interface is successfully initialized, false otherwise.
- **Ownership**: No ownership is transferred.
- **Nullability**: No nullability.

#### shutdownHal
- **Purpose**: Shuts down the HAL interface for the allocator.
- **Type Semantics**: No parameters are required. The function does not return any value.
- **Valid Values**: No valid values.
- **Ownership**: No ownership is transferred.
- **Nullability**: No nullability.

### 3. Return Value
#### allocate
- **Purpose**: Allocates a new graphic buffer based on the provided descriptor and usage flags.
- **Type Semantics**: `AllocationStatus` represents the result of the allocation operation, which can be one of the following: SUCCESS, ERROR_INVALID_DIMENSIONS, ERROR_UNSUPPORTED_FORMAT, or ERROR_GRALLOC_FAILURE.
- **Valid Values**: The return value will indicate whether the allocation was successful or if an error occurred. If successful, a new `GraphicBuffer` object is created and returned through the `outBuffer` parameter.
- **Ownership**: The buffer handle is transferred from the HAL to the allocator, which then manages its lifecycle. The `outBuffer` pointer is set to point to a new `GraphicBuffer` object created using the allocated handle and descriptor.
- **Nullability**: The `outBuffer` parameter can be null if the allocation fails.

#### allocateAsync
- **Purpose**: Allocates a graphic buffer asynchronously, launching a separate thread for the allocation process.
- **Type Semantics**: `AllocationStatus` represents the result of the allocation operation, which can be one of the following: SUCCESS, ERROR_INVALID_DIMENSIONS, ERROR_UNSUPPORTED_FORMAT, or ERROR_GRALLOC_FAILURE.
- **Valid Values**: The return value will indicate whether the allocation was successful or if an error occurred. If successful, a new `GraphicBuffer` object is created and returned through the callback function.
- **Ownership**: The buffer handle is transferred from the HAL to the allocator, which then manages its lifecycle. The `callback` function will be called on a separate thread with the result of the allocation.
- **Nullability**: The `callback` parameter can be null if the allocation fails.

#### free
- **Purpose**: Frees an allocated graphic buffer and removes it from the active list and cache.
- **Type Semantics**: No parameters are required. The function does not return any value.
- **Valid Values**: No valid values.
- **Ownership**: The buffer handle is released back to the HAL, and the `GraphicBuffer` object is destroyed.
- **Nullability**: No nullability.

#### importBuffer
- **Purpose**: Imports an existing graphic buffer from a native handle and adds it to the active list and cache.
- **Type Semantics**: `AllocationStatus` represents the result of the import operation, which can be one of the following: SUCCESS, ERROR_INVALID_DIMENSIONS, ERROR_UNSUPPORTED_FORMAT, or ERROR_GRALLOC_FAILURE.
- **Valid Values**: The return value will indicate whether the import was successful or if an error occurred. If successful, a new `GraphicBuffer` object is created and returned through the `outBuffer` parameter.
- **Ownership**: The buffer handle is transferred from the HAL to the allocator, which then manages its lifecycle. The `outBuffer` pointer is set to point to a new `GraphicBuffer` object created using the imported handle and descriptor.
- **Nullability**: The `outBuffer` parameter can be null if the import fails.

#### get