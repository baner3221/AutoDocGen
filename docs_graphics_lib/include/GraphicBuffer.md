# GraphicBuffer.h

---

| Property | Value |
|----------|-------|
| **Location** | `include\GraphicBuffer.h` |
| **Lines** | 176 |
| **Classes** | 1 |
| **Functions** | 0 |
| **Last Updated** | 2026-01-18 13:28 |

---

## Quick Navigation

### Classes
- [android::graphics::GraphicBuffer](#android-graphics-graphicbuffer)

---

## Documentation for `GraphicBuffer.h`

### 1. Comprehensive Description (2-4 paragraphs)

`GraphicBuffer` is a fundamental class in Android's graphics system, designed to manage allocated graphics memory efficiently. It encapsulates the properties and operations required for handling graphics buffers, including CPU/GPU access, reference counting, and fence synchronization.

The `GraphicBuffer` class provides a high-level interface for interacting with graphics memory, allowing developers to allocate, lock, unlock, and share buffer handles. This is crucial for applications that need to render graphics or process images efficiently, leveraging the power of Android's hardware acceleration capabilities.

### 2. Parameters (DETAILED for each)

#### `GraphicBuffer(const BufferDescriptor& descriptor, NativeHandle handle, IBufferAllocator* allocator)`

- **Purpose**: Constructs a new `GraphicBuffer` object with specified properties and native buffer handle.
- **Type Semantics**: `BufferDescriptor` describes the geometry and format of the buffer, while `NativeHandle` is a platform-specific handle to the underlying graphics memory.
- **Valid Values**: The `descriptor` must contain valid dimensions, stride, and pixel format. The `handle` should be a valid native handle from an allocator that supports the specified descriptor.
- **Ownership**: The `BufferDescriptor`, `NativeHandle`, and `IBufferAllocator` are owned by the caller and passed to the constructor. The `GraphicBuffer` object takes ownership of these resources.
- **Nullability**: The `descriptor` and `handle` cannot be null. If either is null, the constructor will throw an exception.

#### `GraphicBuffer(GraphicBuffer&& other) noexcept`

- **Purpose**: Move constructor for efficient buffer transfer.
- **Type Semantics**: Moves the state of one `GraphicBuffer` object to another without copying memory.
- **Valid Values**: The source `GraphicBuffer` must be in a valid state and not already moved or destroyed.
- **Ownership**: The source `GraphicBuffer` is transferred to the new object, and its resources are released. The destination `GraphicBuffer` takes ownership of these resources.
- **Nullability**: The source `GraphicBuffer` cannot be null. If it is null, the move constructor will throw an exception.

#### `~GraphicBuffer()`

- **Purpose**: Destructor for releasing the buffer back to the allocator.
- **Type Semantics**: Frees any allocated memory and releases the native handle.
- **Valid Values**: The `GraphicBuffer` object must be in a valid state before destruction.
- **Ownership**: The `GraphicBuffer` object is responsible for releasing its resources, including the native handle and any associated fences.
- **Nullability**: The `GraphicBuffer` cannot be null. If it is null, the destructor will throw an exception.

#### `lockForRead(MappedRegion& outRegion)`

- **Purpose**: Locks the buffer for CPU read access.
- **Type Semantics**: Returns a pointer to the mapped memory region that can be used for reading data from the buffer.
- **Valid Values**: The buffer must be unlocked before locking. The `MappedRegion` object is populated with information about the locked memory.
- **Ownership**: The caller owns the `MappedRegion` object and is responsible for releasing it when done.
- **Nullability**: If the lock fails, the `outRegion` will not be modified.

#### `lockForWrite(MappedRegion& outRegion)`

- **Purpose**: Locks the buffer for CPU write access.
- **Type Semantics**: Returns a pointer to the mapped memory region that can be used for writing data to the buffer.
- **Valid Values**: The buffer must be unlocked before locking. The `MappedRegion` object is populated with information about the locked memory.
- **Ownership**: The caller owns the `MappedRegion` object and is responsible for releasing it when done.
- **Nullability**: If the lock fails, the `outRegion` will not be modified.

#### `lockRegion(uint32_t x, uint32_t y, uint32_t width, uint32_t height, MappedRegion& outRegion)`

- **Purpose**: Locks a specific region of the buffer for CPU access.
- **Type Semantics**: Returns a pointer to the mapped memory region that can be used for reading or writing data within the specified region.
- **Valid Values**: The buffer must be unlocked before locking. The `MappedRegion` object is populated with information about the locked memory.
- **Ownership**: The caller owns the `MappedRegion` object and is responsible for releasing it when done.
- **Nullability**: If the lock fails, the `outRegion` will not be modified.

#### `unlock()`

- **Purpose**: Unlocks the buffer, flushing any writes to GPU resources.
- **Type Semantics**: Returns a boolean indicating whether the unlock operation was successful.
- **Valid Values**: The buffer must be locked before unlocking. The buffer is unlocked and can now be accessed by other threads or processes.
- **Ownership**: No ownership changes occur during this operation.
- **Nullability**: If the unlock fails, the function will return false.

#### `duplicateHandle() const`

- **Purpose**: Creates a duplicate of the native handle for sharing.
- **Type Semantics**: Returns a new `NativeHandle` that is a copy of the original buffer's handle.
- **Valid Values**: The buffer must be in a valid state and not already duplicated.
- **Ownership**: The caller owns the returned `NativeHandle`. It should be released using the appropriate native handle management functions when no longer needed.
- **Nullability**: If the duplicate fails, the function will return null.

#### `incRef()`

- **Purpose**: Increments the reference count of the buffer.
- **Type Semantics**: Increases the internal reference counter to keep track of how many objects are using this buffer.
- **Valid Values**: The buffer must be in a valid state and not already destroyed.
- **Ownership**: No ownership changes occur during this operation.
- **Nullability**: If the increment fails, the function will return false.

#### `decRef()`

- **Purpose**: Decrements the reference count of the buffer and checks if it should be deleted.
- **Type Semantics**: Decreases the internal reference counter. If the counter reaches zero, the buffer is released back to the allocator.
- **Valid Values**: The buffer must be in a valid state and not already destroyed.
- **Ownership**: No ownership changes occur during this operation.
- **Nullability**: If the decrement fails, the function will return false.

#### `getRefCount() const`

- **Purpose**: Retrieves the current reference count of the buffer.
- **Type Semantics**: Returns an integer representing the number of objects currently using this buffer.
- **Valid Values**: The buffer must be in a valid state and not already destroyed.
- **Ownership**: No ownership changes occur during this operation.
- **Nullability**: If the function fails, it will return -1.

#### `getDescriptor() const`

- **Purpose**: Retrieves the descriptor of the buffer, which includes its geometry, format, stride, and usage flags.
- **Type Semantics**: Returns a constant reference to a `BufferDescriptor` object that describes the buffer's properties.
- **Valid Values**: The buffer must be in a valid state and not already destroyed.
- **Ownership**: No ownership changes occur during this operation.
- **Nullability**: If the function fails, it will return an invalid descriptor.

#### `getWidth() const`

- **Purpose**: Retrieves the width of the buffer in pixels.
- **Type Semantics**: Returns an integer representing the width of the buffer.
- **Valid Values**: The buffer must be in a valid state and not already destroyed.
- **Ownership**: No ownership changes occur during this operation.
- **Nullability**: If the function fails, it will return 0.

#### `getHeight() const`

- **Purpose**: Retrieves the height of the buffer in pixels.
- **Type Semantics**: Returns an integer representing the height of the buffer.
- **Valid Values**: The buffer must be in a valid state and not already destroyed.
- **Ownership**: No ownership changes occur during this operation.
- **Nullability**: If the function fails, it will return 0.

#### `getStride() const`

- **Purpose**: Retrieves the stride of the buffer in bytes.
- **Type Semantics**: Returns an integer representing the number of bytes between consecutive rows of the buffer.
- **Valid Values**: The buffer must be in a valid state and not already destroyed.
- **Ownership**: No ownership changes occur during this operation.
- **Nullability**: If the function fails, it will return 0.

#### `getFormat() const`

- **Purpose**: Retrieves the pixel format of the buffer.
- **Type Semantics**: Returns a value from the `PixelFormat` enum representing the color and depth information of the buffer.
- **Valid Values**: The buffer must be in a valid state and not already destroyed.
- **Ownership**: No ownership changes occur during this operation.
- **Nullability**: If the function fails, it will return an invalid format.

#### `getUsage() const`

- **Purpose**: Retrieves the usage flags of the buffer, indicating how it is intended to be used (e.g., for rendering or video processing).
- **Type Semantics**: Returns a value from the `BufferUsage` enum representing the buffer's intended use.
- **Valid Values**: The buffer must be in a valid state and not already destroyed.
- **Ownership**: No ownership changes occur during this operation.
- **Nullability**: If the function fails, it will return an invalid usage.

#### `getNativeHandle() const`

- **Purpose**: Retrieves the native handle of the buffer, which is used to interact with the underlying graphics memory.
- **Type Semantics**: Returns a constant reference to a `NativeHandle` object representing the buffer's handle.
- **Valid Values**: The buffer must be in a valid state and