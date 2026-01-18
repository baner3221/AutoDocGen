# GraphicBuffer.cpp

---

| Property | Value |
|----------|-------|
| **Location** | `src\GraphicBuffer.cpp` |
| **Lines** | 221 |
| **Classes** | 0 |
| **Functions** | 0 |
| **Last Updated** | 2026-01-18 13:28 |

---

## Documentation for `GraphicBuffer.cpp`

### 1. Comprehensive Description (2-4 paragraphs)
The `GraphicBuffer` class in the Android graphics buffer library is responsible for managing a buffer of pixel data, including its dimensions, format, and memory handle. It provides methods to lock the buffer for reading or writing, unlock it, duplicate its handle, and manage reference counting. The class also handles fences associated with the buffer's acquisition.

### 2. Parameters (DETAILED for each)
#### `GraphicBuffer::GraphicBuffer(const BufferDescriptor& descriptor, NativeHandle handle, IBufferAllocator* allocator)`
- **Purpose**: Initializes a new `GraphicBuffer` instance with the specified buffer descriptor, memory handle, and allocator.
- **Type Semantics**: 
  - `const BufferDescriptor&`: A reference to a constant buffer descriptor object that describes the properties of the buffer (e.g., width, height, format).
  - `NativeHandle`: An opaque structure representing a native memory handle. It contains file descriptors and integers for accessing the buffer's memory.
  - `IBufferAllocator*`: A pointer to an allocator interface responsible for managing the buffer's lifecycle.
- **Valid Values**: 
  - `BufferDescriptor` must have valid dimensions (width > 0, height > 0) and a non-UNKNOWN format.
  - `NativeHandle` should be a valid memory handle that can be accessed by the system.
  - `IBufferAllocator` must be a valid pointer to an allocator interface.
- **Ownership**: 
  - `BufferDescriptor` is borrowed (not owned).
  - `NativeHandle` is borrowed (not owned).
  - `IBufferAllocator*` is transferred (owned).
- **Nullability**: 
  - `BufferDescriptor` can be null, but it must have valid dimensions and format.
  - `NativeHandle` can be null, but it should not be used if the buffer is not valid.
  - `IBufferAllocator*` cannot be null.

#### `GraphicBuffer::GraphicBuffer(GraphicBuffer&& other) noexcept`
- **Purpose**: Moves an existing `GraphicBuffer` instance to a new one.
- **Type Semantics**: 
  - `GraphicBuffer&&`: A rvalue reference to the source `GraphicBuffer`.
- **Valid Values**: 
  - The source `GraphicBuffer` must be valid and not already moved or destroyed.
- **Ownership**: 
  - `BufferDescriptor`, `NativeHandle`, `allocator_`, `mappedRegion_`, `refCount_`, `bufferId_`, `fenceManager_`, and `acquireFenceFd_` are transferred (owned).
- **Nullability**: 
  - The source `GraphicBuffer` can be null, but it must not already moved or destroyed.

#### `GraphicBuffer::~GraphicBuffer()`
- **Purpose**: Cleans up the `GraphicBuffer` instance.
- **Type Semantics**: 
  - No parameters.
- **Valid Values**: 
  - The `GraphicBuffer` instance must be valid and not already destroyed.
- **Ownership**: 
  - All resources are released (e.g., memory, fences).
- **Nullability**: 
  - The `GraphicBuffer` can be null.

#### `bool GraphicBuffer::lockForRead(MappedRegion& outRegion)`
- **Purpose**: Locks the buffer for reading and returns a mapped region.
- **Type Semantics**: 
  - `MappedRegion&`: A reference to an output parameter that will hold the locked mapped region.
- **Valid Values**: 
  - The buffer must be valid and not already locked.
- **Ownership**: 
  - `MappedRegion` is borrowed (not owned).
- **Nullability**: 
  - `MappedRegion` can be null.

#### `bool GraphicBuffer::lockForWrite(MappedRegion& outRegion)`
- **Purpose**: Locks the buffer for writing and returns a mapped region.
- **Type Semantics**: 
  - `MappedRegion&`: A reference to an output parameter that will hold the locked mapped region.
- **Valid Values**: 
  - The buffer must be valid and not already locked.
- **Ownership**: 
  - `MappedRegion` is borrowed (not owned).
- **Nullability**: 
  - `MappedRegion` can be null.

#### `bool GraphicBuffer::lockRegion(uint32_t x, uint32_t y, uint32_t width, uint32_t height, MappedRegion& outRegion)`
- **Purpose**: Locks a specific region of the buffer for reading or writing and returns a mapped region.
- **Type Semantics**: 
  - `uint32_t`: The x-coordinate of the top-left corner of the region.
  - `uint32_t`: The y-coordinate of the top-left corner of the region.
  - `uint32_t`: The width of the region.
  - `uint32_t`: The height of the region.
  - `MappedRegion&`: A reference to an output parameter that will hold the locked mapped region.
- **Valid Values**: 
  - The buffer must be valid and not already locked.
  - The specified region must be within the bounds of the buffer.
- **Ownership**: 
  - `MappedRegion` is borrowed (not owned).
- **Nullability**: 
  - `MappedRegion` can be null.

#### `bool GraphicBuffer::unlock()`
- **Purpose**: Unlocks the buffer and releases any mapped regions.
- **Type Semantics**: 
  - No parameters.
- **Valid Values**: 
  - The buffer must be valid and locked.
- **Ownership**: 
  - All mapped regions are released (e.g., memory).
- **Nullability**: 
  - The `GraphicBuffer` can be null.

#### `NativeHandle GraphicBuffer::duplicateHandle() const`
- **Purpose**: Duplicates the buffer's memory handle.
- **Type Semantics**: 
  - `NativeHandle`: An opaque structure representing a duplicated memory handle.
- **Valid Values**: 
  - The buffer must be valid and not already moved or destroyed.
- **Ownership**: 
  - The returned `NativeHandle` is borrowed (not owned).
- **Nullability**: 
  - The buffer can be null.

#### `void GraphicBuffer::incRef()`
- **Purpose**: Increments the reference count of the `GraphicBuffer`.
- **Type Semantics**: 
  - No parameters.
- **Valid Values**: 
  - The `GraphicBuffer` must be valid and not already destroyed.
- **Ownership**: 
  - No ownership changes.
- **Nullability**: 
  - The `GraphicBuffer` can be null.

#### `bool GraphicBuffer::decRef()`
- **Purpose**: Decrements the reference count of the `GraphicBuffer`.
- **Type Semantics**: 
  - No parameters.
- **Valid Values**: 
  - The `GraphicBuffer` must be valid and not already destroyed.
- **Ownership**: 
  - If the reference count reaches zero, the buffer is freed (e.g., memory).
- **Nullability**: 
  - The `GraphicBuffer` can be null.

#### `int32_t GraphicBuffer::getRefCount() const`
- **Purpose**: Returns the current reference count of the `GraphicBuffer`.
- **Type Semantics**: 
  - `int32_t`: An integer representing the reference count.
- **Valid Values**: 
  - The `GraphicBuffer` must be valid and not already destroyed.
- **Ownership**: 
  - No ownership changes.
- **Nullability**: 
  - The `GraphicBuffer` can be null.

#### `void GraphicBuffer::setAcquireFence(FenceManager* fenceManager, int fenceFd)`
- **Purpose**: Sets the fence manager and fence file descriptor for the buffer.
- **Type Semantics**: 
  - `FenceManager*`: A pointer to a fence manager interface.
  - `int`: The file descriptor of the fence.
- **Valid Values**: 
  - `FenceManager` must be a valid pointer to an fence manager interface.
  - `fenceFd` should be a valid file descriptor or -1 if no fence is set.
- **Ownership**: 
  - `FenceManager*` is transferred (owned).
- **Nullability**: 
  - `FenceManager*` can be null.

#### `bool GraphicBuffer::waitAcquireFence(uint32_t timeoutMs)`
- **Purpose**: Waits for the buffer's acquire fence to signal.
- **Type Semantics**: 
  - `uint32_t`: The maximum time in milliseconds to wait for the fence to signal.
- **Valid Values**: 
  - `timeoutMs` should be a non-negative integer or 0 to wait indefinitely.
- **Ownership**: 
  - No ownership changes.
- **Nullability**: 
  - The `GraphicBuffer` can be null.

### 3. Return Value
#### `GraphicBuffer::GraphicBuffer(const BufferDescriptor& descriptor, NativeHandle handle, IBufferAllocator* allocator)`
- **Representation**: A new `GraphicBuffer` instance.
- **All Possible Return States**: Success.
- **Error Conditions and How They're Indicated**: None.
- **Ownership of Returned Objects**: The returned `GraphicBuffer` is owned.

#### `GraphicBuffer::GraphicBuffer(GraphicBuffer&& other) noexcept`
- **Representation**: A new `GraphicBuffer` instance.
- **All Possible Return States**: Success.
- **Error Conditions and How They're Indicated**: None.
- **Ownership of Returned Objects**: The returned `GraphicBuffer` is owned.

#### `GraphicBuffer::~GraphicBuffer()`
- **Representation**: No return value.
- **All Possible Return States**: Success.
- **Error Conditions and How They're Indicated**: None.
- **Ownership of Returned Objects**: All resources are released (e.g., memory,