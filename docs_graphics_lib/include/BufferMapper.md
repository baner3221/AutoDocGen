# BufferMapper.h

---

| Property | Value |
|----------|-------|
| **Location** | `include\BufferMapper.h` |
| **Lines** | 185 |
| **Classes** | 2 |
| **Functions** | 0 |
| **Last Updated** | 2026-01-18 13:28 |

---

## Quick Navigation

### Classes
- [android::graphics::BufferLockGuard](#android-graphics-bufferlockguard)
- [android::graphics::BufferMapper](#android-graphics-buffermapper)

---

## Documentation for `BufferMapper.h`

### 1. Comprehensive Description (2-4 paragraphs)
The `BufferMapper` class provides a high-level utility for simplified buffer CPU access in Android applications. It offers RAII-style locking and convenience methods for common buffer manipulation tasks such as copying data, filling buffers, and processing buffer contents. This class is particularly useful for developers who need to interact with graphics buffers efficiently without dealing with low-level memory management.

### 2. Parameters (DETAILED for each)
#### BufferLockGuard
- **Purpose**: Manages the locking of a `GraphicBuffer` object for CPU access.
- **Type Semantics**: A lock guard that ensures the buffer is locked during its lifetime and unlocked when it goes out of scope.
- **Valid Values**: The lock mode can be one of three options: Read, Write, or ReadWrite. These modes determine whether the buffer should be read-only, write-only, or both.
- **Ownership**: The `GraphicBuffer` object is owned by the caller and must remain valid throughout the lifetime of the `BufferLockGuard`.
- **Nullability**: The `GraphicBuffer` pointer cannot be null.

#### BufferMapper
- **Purpose**: Provides utility functions for common buffer operations such as copying data, filling buffers, and processing buffer contents.
- **Type Semantics**: A collection of static methods that perform various buffer manipulation tasks.
- **Valid Values**: None.
- **Ownership**: The `BufferMapper` class itself does not own any resources.
- **Nullability**: None.

### 3. Return Value
#### BufferLockGuard
- **Purpose**: Indicates whether the lock was successfully acquired.
- **Type Semantics**: A boolean value (`true` if locked, `false` otherwise).
- **Valid Values**: True or false.
- **Ownership**: None.
- **Nullability**: None.

#### BufferMapper
- **Purpose**: Returns the number of bytes copied during a data copy operation.
- **Type Semantics**: An integer representing the number of bytes successfully copied.
- **Valid Values**: Any non-negative integer.
- **Ownership**: None.
- **Nullability**: None.

### 4. Dependencies Cross-Reference
- `GraphicBuffer`: The class used for buffer management and access.
- `MappedRegion`: A structure that holds information about a mapped region of a buffer.
- `std::function<void(void* data, size_t size)>`: A function object that can be passed to the `processBuffer` method.

### 5. Side Effects
#### BufferLockGuard
- **State Modifications**: The buffer is locked during its lifetime and unlocked when it goes out of scope.
- **Locks Acquired/Released**: The buffer is locked on construction and unlocked on destruction.
- **I/O Operations**: None.
- **Signals/Events Emitted**: None.

#### BufferMapper
- **State Modifications**: None.
- **Locks Acquired/Released**: None.
- **I/O Operations**: Data copying, filling, and processing operations may involve I/O operations with the buffer.
- **Signals/Events Emitted**: None.

### 6. Usage Context
The `BufferMapper` class is typically used in scenarios where direct access to graphics buffers is required for rendering or data manipulation tasks. It is commonly used by applications that need to process image data, perform texture uploads, or handle video frames.

### 7. Related Functions
| Relationship Type | Function Name | Description |
|------------------|--------------|-------------|
| Uses             | `GraphicBuffer` | For managing and accessing buffer data. |
| Uses             | `MappedRegion` | For storing information about a mapped region of a buffer. |
| Uses             | `std::function<void(void* data, size_t size)>` | For passing a callback function to the `processBuffer` method. |

### 8. Code Example
```cpp
// Example usage of BufferMapper for copying data from a buffer to CPU memory
GraphicBuffer* buffer = ...; // Assume this is a valid GraphicBuffer object
void* dest = ...; // Assume this is a valid destination memory location

size_t bytesCopied = android::graphics::BufferMapper::copyFromBuffer(buffer, dest, 1024);
if (bytesCopied > 0) {
    // Process the copied data...
}
```

This example demonstrates how to use the `BufferMapper` class to copy data from a `GraphicBuffer` object to CPU memory. The `copyFromBuffer` method is called with the buffer, destination memory location, and maximum number of bytes to copy. If the copy operation is successful, the number of bytes copied is returned, and the data can be processed further.