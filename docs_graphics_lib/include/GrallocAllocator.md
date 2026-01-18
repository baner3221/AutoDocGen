# GrallocAllocator.h

---

| Property | Value |
|----------|-------|
| **Location** | `include\GrallocAllocator.h` |
| **Lines** | 194 |
| **Classes** | 2 |
| **Functions** | 0 |
| **Last Updated** | 2026-01-18 13:28 |

---

## Quick Navigation

### Classes
- [android::graphics::GrallocAllocator](#android-graphics-grallocallocator)
- [android::graphics::GrallocMapper](#android-graphics-grallocmapper)

---

## Documentation for `GrallocAllocator.h`

### Comprehensive Description (2-4 paragraphs)
The `GrallocAllocator` class is a high-level buffer allocator that leverages the Android HAL to manage graphics buffers efficiently. It supports both gralloc 2.x and AIDL-based interfaces, allowing it to adapt to different hardware versions. The allocator automatically detects the appropriate HAL version and caches allocated buffers for performance optimization. It also provides asynchronous allocation support through a thread pool, enabling efficient resource management in multi-threaded environments.

### Parameters (DETAILED for each)
#### GrallocAllocator()
- **Purpose**: Initializes a `GrallocAllocator` instance with automatic HAL detection.
- **Type Semantics**: No specific type semantics as it is a constructor.
- **Valid Values**: None.
- **Ownership**: The allocator owns the underlying resources and handles.
- **Nullability**: None.

#### GrallocAllocator(GrallocVersion version)
- **Purpose**: Initializes a `GrallocAllocator` instance targeting a specific HAL version.
- **Type Semantics**: Takes an enum value representing the desired gralloc version.
- **Valid Values**: Must be one of `GRALLOC_2_0`, `GRALLOC_3_0`, `GRALLOC_4_0`, or `GRALLOC_AIDL`.
- **Ownership**: The allocator owns the underlying resources and handles.
- **Nullability**: None.

#### ~GrallocAllocator()
- **Purpose**: Destructor for the `GrallocAllocator` class. It releases all allocated resources and shuts down the HAL connection.
- **Type Semantics**: No specific type semantics as it is a destructor.
- **Valid Values**: None.
- **Ownership**: The allocator owns the underlying resources and handles.
- **Nullability**: None.

#### allocate(const BufferDescriptor& descriptor, std::unique_ptr<GraphicBuffer>& outBuffer)
- **Purpose**: Allocates a buffer based on the provided `BufferDescriptor`.
- **Type Semantics**: Takes a `BufferDescriptor` object and returns a `std::unique_ptr<GraphicBuffer>`.
- **Valid Values**: The `BufferDescriptor` must contain valid dimensions, format, and usage flags.
- **Ownership**: The allocator transfers ownership of the allocated buffer to the caller.
- **Nullability**: If allocation fails, `outBuffer` remains null.

#### allocateAsync(const BufferDescriptor& descriptor, AllocationCallback callback)
- **Purpose**: Asynchronously allocates a buffer based on the provided `BufferDescriptor`.
- **Type Semantics**: Takes a `BufferDescriptor` object and an `AllocationCallback` function.
- **Valid Values**: The `BufferDescriptor` must contain valid dimensions, format, and usage flags. The `AllocationCallback` should be a callable that takes a `GraphicBuffer*` as its parameter.
- **Ownership**: The allocator does not transfer ownership of the allocated buffer to the caller; instead, it calls the callback function when allocation is complete.
- **Nullability**: If allocation fails, the callback is called with a null pointer.

#### free(GraphicBuffer* buffer)
- **Purpose**: Frees an allocated buffer.
- **Type Semantics**: Takes a `GraphicBuffer*` object.
- **Valid Values**: The buffer must be valid and owned by the allocator.
- **Ownership**: The allocator releases ownership of the buffer.
- **Nullability**: If the buffer is null, the function does nothing.

#### importBuffer(const NativeHandle& handle, const BufferDescriptor& descriptor, std::unique_ptr<GraphicBuffer>& outBuffer)
- **Purpose**: Imports an existing buffer from a native handle into a `GraphicBuffer`.
- **Type Semantics**: Takes a `NativeHandle`, a `BufferDescriptor`, and returns a `std::unique_ptr<GraphicBuffer>`.
- **Valid Values**: The `NativeHandle` must be valid, the `BufferDescriptor` must match the buffer's dimensions, format, and usage flags.
- **Ownership**: The allocator transfers ownership of the imported buffer to the caller.
- **Nullability**: If import fails, `outBuffer` remains null.

#### getSupportedUsage() const
- **Purpose**: Returns a bitmask representing supported buffer usages.
- **Type Semantics**: Returns an unsigned integer (bitmask).
- **Valid Values**: The returned value is a combination of valid buffer usage flags.
- **Ownership**: None.
- **Nullability**: None.

#### isFormatSupported(PixelFormat format, BufferUsage usage) const
- **Purpose**: Checks if a specific pixel format and usage are supported.
- **Type Semantics**: Takes a `PixelFormat` and a `BufferUsage`.
- **Valid Values**: The `PixelFormat` must be valid, the `BufferUsage` must be one of the supported flags.
- **Ownership**: None.
- **Nullability**: None.

#### getVersion() const
- **Purpose**: Returns the detected gralloc version.
- **Type Semantics**: Returns a `GrallocVersion` enum value.
- **Valid Values**: One of `GRALLOC_2_0`, `GRALLOC_3_0`, `GRALLOC_4_0`, or `GRALLOC_AIDL`.
- **Ownership**: None.
- **Nullability**: None.

#### getMapper() const
- **Purpose**: Returns a pointer to the underlying buffer mapper for direct access.
- **Type Semantics**: Returns a `GrallocMapper*`.
- **Valid Values**: The returned pointer is valid and owned by the allocator.
- **Ownership**: The allocator owns the underlying resources and handles.
- **Nullability**: If the mapper is not available, returns null.

#### queryFormatInfo(PixelFormat format, BufferUsage usage, uint32_t& outStride) const
- **Purpose**: Queries implementation-defined format information for a specific pixel format and usage.
- **Type Semantics**: Takes a `PixelFormat`, a `BufferUsage`, and an output parameter `outStride`.
- **Valid Values**: The `PixelFormat` must be valid, the `BufferUsage` must be one of the supported flags. The `outStride` should be initialized to a default value.
- **Ownership**: None.
- **Nullability**: If the query fails, `outStride` remains unchanged.

#### dumpState() const
- **Purpose**: Dumps the current state of the allocator for debugging purposes.
- **Type Semantics**: Returns a string containing debug information.
- **Valid Values**: The returned string contains relevant details about the allocator's internal state.
- **Ownership**: None.
- **Nullability**: None.

### Return Value
#### GrallocAllocator()
- **Purpose**: Initializes a `GrallocAllocator` instance with automatic HAL detection.
- **Type Semantics**: No specific type semantics as it is a constructor.
- **Valid Values**: None.
- **Ownership**: The allocator owns the underlying resources and handles.
- **Nullability**: None.

#### GrallocAllocator(GrallocVersion version)
- **Purpose**: Initializes a `GrallocAllocator` instance targeting a specific HAL version.
- **Type Semantics**: Takes an enum value representing the desired gralloc version.
- **Valid Values**: Must be one of `GRALLOC_2_0`, `GRALLOC_3_0`, `GRALLOC_4_0`, or `GRALLOC_AIDL`.
- **Ownership**: The allocator owns the underlying resources and handles.
- **Nullability**: None.

#### ~GrallocAllocator()
- **Purpose**: Destructor for the `GrallocAllocator` class. It releases all allocated resources and shuts down the HAL connection.
- **Type Semantics**: No specific type semantics as it is a destructor.
- **Valid Values**: None.
- **Ownership**: The allocator owns the underlying resources and handles.
- **Nullability**: None.

#### allocate(const BufferDescriptor& descriptor, std::unique_ptr<GraphicBuffer>& outBuffer)
- **Purpose**: Allocates a buffer based on the provided `BufferDescriptor`.
- **Type Semantics**: Takes a `BufferDescriptor` object and returns a `std::unique_ptr<GraphicBuffer>`.
- **Valid Values**: The `BufferDescriptor` must contain valid dimensions, format, and usage flags.
- **Ownership**: The allocator transfers ownership of the allocated buffer to the caller.
- **Nullability**: If allocation fails, `outBuffer` remains null.

#### allocateAsync(const BufferDescriptor& descriptor, AllocationCallback callback)
- **Purpose**: Asynchronously allocates a buffer based on the provided `BufferDescriptor`.
- **Type Semantics**: Takes a `BufferDescriptor` object and an `AllocationCallback` function.
- **Valid Values**: The `BufferDescriptor` must contain valid dimensions, format, and usage flags. The `AllocationCallback` should be a callable that takes a `GraphicBuffer*` as its parameter.
- **Ownership**: The allocator does not transfer ownership of the allocated buffer to the caller; instead, it calls the callback function when allocation is complete.
- **Nullability**: If allocation fails, the callback is called with a null pointer.

#### free(GraphicBuffer* buffer)
- **Purpose**: Frees an allocated buffer.
- **Type Semantics**: Takes a `GraphicBuffer*` object.
- **Valid Values**: The buffer must be valid and owned by the allocator.
- **Ownership**: The allocator releases ownership of the buffer.
- **Nullability**: If the buffer is null, the function does nothing.

#### importBuffer(const NativeHandle& handle, const BufferDescriptor& descriptor, std::unique_ptr<GraphicBuffer>& outBuffer)
- **Purpose**: Imports an existing buffer from a native handle into a `GraphicBuffer`.
- **Type Semantics**: Takes a `NativeHandle`, a `BufferDescriptor`, and returns a `std::unique_ptr<GraphicBuffer>`.
- **Valid Values**: The `NativeHandle` must be valid, the `BufferDescriptor` must match the buffer's dimensions, format, and usage flags.
- **Ownership**: The allocator transfers ownership of the imported buffer to the caller