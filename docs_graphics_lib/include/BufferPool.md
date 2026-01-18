# BufferPool.h

---

| Property | Value |
|----------|-------|
| **Location** | `include\BufferPool.h` |
| **Lines** | 191 |
| **Classes** | 3 |
| **Functions** | 0 |
| **Last Updated** | 2026-01-18 13:28 |

---

## Quick Navigation

### Classes
- [android::graphics::BufferPoolConfig](#android-graphics-bufferpoolconfig)
- [android::graphics::BufferPool](#android-graphics-bufferpool)
- [android::graphics::BufferPoolListener](#android-graphics-bufferpoollistener)

---

## Comprehensive Description (2-4 paragraphs)

The `BufferPool` class in the Android graphics buffer library manages a collection of pre-allocated buffers to reduce allocation latency, which is crucial for camera streaming and video playback scenarios. It provides features such as pre-allocation, automatic pool growth, buffer reuse with format validation, statistics collection, and listener callbacks for pool events.

### Why does it exist? What problem does it solve?

The `BufferPool` class solves the problem of frequent buffer allocations in high-performance applications like camera streaming and video playback. By pre-allocating a fixed number of buffers during initialization, the class reduces the latency associated with buffer allocation by avoiding the overhead of repeatedly creating new objects. This is particularly beneficial for scenarios where performance is critical.

### How does it fit into the larger workflow?

The `BufferPool` class integrates seamlessly into the Android graphics framework. It is used by various components such as camera drivers, video decoders, and renderers to manage buffers efficiently. The pool's ability to grow automatically when needed ensures that there are always enough buffers available for immediate use, without the need for frequent reallocations.

### Key algorithms or techniques used

- **Pre-allocation**: Buffers are allocated during initialization and stored in a vector.
- **Automatic growth**: When the pool is empty and `allowBlocking` is true, it attempts to grow the pool by allocating additional buffers.
- **Buffer reuse**: Reused buffers are validated against the current descriptor before being returned to the pool.
- **Statistics collection**: The class maintains statistics on the number of free and total buffers.

## Parameters (DETAILED for each)

### `allocator_`
- **Purpose**: Provides an interface for buffer creation.
- **Type Semantics**: A shared pointer to an `IBufferAllocator` object.
- **Valid Values**: Any valid implementation of `IBufferAllocator`.
- **Ownership**: Transferred. The `BufferPool` takes ownership of the allocator.
- **Nullability**: Can be null, but this would lead to undefined behavior.

### `descriptor_`
- **Purpose**: Specifies the buffer format for all pool buffers.
- **Type Semantics**: A `BufferDescriptor` object.
- **Valid Values**: Any valid buffer descriptor that matches the requirements of the application.
- **Ownership**: Borrowed. The `BufferPool` does not own the descriptor.
- **Nullability**: Can be null, but this would lead to undefined behavior.

### `config_`
- **Purpose**: Configures the pool's behavior, such as minimum and maximum buffers, pre-allocation count, growth count, blocking behavior, and timeout for blocking acquire.
- **Type Semantics**: A `BufferPoolConfig` object.
- **Valid Values**: Any valid configuration that meets the application's requirements.
- **Ownership**: Transferred. The `BufferPool` takes ownership of the config.
- **Nullability**: Can be null, but this would lead to default values being used.

### `allBuffers_`
- **Purpose**: Stores all allocated buffers in a vector.
- **Type Semantics**: A vector of unique pointers to `GraphicBuffer` objects.
- **Valid Values**: Any valid buffer that matches the descriptor and configuration.
- **Ownership**: Transferred. The `BufferPool` takes ownership of each buffer.
- **Nullability**: Can be null, but this would lead to undefined behavior.

### `freeBuffers_`
- **Purpose**: Maintains a queue of free buffers for immediate reuse.
- **Type Semantics**: A queue of pointers to `GraphicBuffer` objects.
- **Valid Values**: Any valid buffer that matches the descriptor and configuration.
- **Ownership**: Transferred. The `BufferPool` takes ownership of each buffer.
- **Nullability**: Can be null, but this would lead to undefined behavior.

### `mutex_`
- **Purpose**: Provides thread safety for accessing shared resources like `allBuffers_`, `freeBuffers_`, and `listeners_`.
- **Type Semantics**: A mutex object.
- **Valid Values**: Any valid mutex implementation.
- **Ownership**: Transferred. The `BufferPool` takes ownership of the mutex.
- **Nullability**: Can be null, but this would lead to undefined behavior.

### `bufferAvailable_`
- **Purpose**: Used for signaling when a buffer becomes available in the pool.
- **Type Semantics**: A condition variable object.
- **Valid Values**: Any valid condition variable implementation.
- **Ownership**: Transferred. The `BufferPool` takes ownership of the condition variable.
- **Nullability**: Can be null, but this would lead to undefined behavior.

### `listeners_`
- **Purpose**: Stores pointers to listeners that are notified of pool events.
- **Type Semantics**: A vector of pointers to `BufferPoolListener` objects.
- **Valid Values**: Any valid implementation of `BufferPoolListener`.
- **Ownership**: Transferred. The `BufferPool` takes ownership of each listener.
- **Nullability**: Can be null, but this would lead to undefined behavior.

### `stats_`
- **Purpose**: Collects statistics on the pool's state, such as free and total buffers.
- **Type Semantics**: A `PoolStatistics` object.
- **Valid Values**: Any valid statistics collection mechanism.
- **Ownership**: Transferred. The `BufferPool` takes ownership of the stats.
- **Nullability**: Can be null, but this would lead to undefined behavior.

## Return Value

- **Purpose**: Returns a pointer to a `GraphicBuffer` object from the pool.
- **Type Semantics**: A pointer to a `GraphicBuffer` object.
- **Valid Values**: Any valid buffer that matches the descriptor and configuration.
- **Ownership**: Transferred. The caller takes ownership of the buffer.
- **Nullability**: Can be null if no buffers are available or if an error occurs.

## Dependencies Cross-Reference

- **`IBufferAllocator`**:
  - Used to create new `GraphicBuffer` objects.
  - [IBufferAllocator::createBuffer()](#ibufferallocator-createbuffer)

- **`BufferDescriptor`**:
  - Specifies the format and dimensions of the buffers in the pool.
  - [BufferDescriptor::BufferDescriptor()](#bufferdescriptor-bufferdescriptor)

- **`BufferPoolConfig`**:
  - Configures the pool's behavior, such as minimum and maximum buffers, pre-allocation count, growth count, blocking behavior, and timeout for blocking acquire.
  - [BufferPoolConfig::BufferPoolConfig()](#bufferpoolconfig-bufferpoolconfig)

## Side Effects

- **State Modifications**: Modifies the state of the `allBuffers_`, `freeBuffers_`, and `listeners_` vectors.
- **Locks Acquired/Released**: Acquires and releases locks on `mutex_`.
- **I/O Operations**: Performs I/O operations to communicate with the underlying buffer allocator.
- **Signals/Events Emitted**: Emits signals or events through listeners.

## Usage Context

The `BufferPool` class is typically used in high-performance applications like camera drivers, video decoders, and renderers. It is called when a new buffer is needed for processing, and it returns the buffer to the pool once it is no longer required.

### Prerequisites

- The application must have access to an `IBufferAllocator` implementation.
- The application must have a valid `BufferDescriptor` object that matches the requirements of the buffers in the pool.

### Typical Callers

- Camera drivers
- Video decoders
- Renderers

## Related Functions

| Relationship Type | Function Name | Description |
| --- | --- | --- |
| Inherits from | RefBase | Provides reference counting and lifecycle management. |

## Code Example

```cpp
#include "BufferPool.h"

int main() {
    // Create an IBufferAllocator instance (e.g., using SurfaceFlinger)
    std::shared_ptr<IBufferAllocator> allocator = ...;

    // Define a buffer descriptor (e.g., for YUV420P format)
    BufferDescriptor descriptor;
    descriptor.format = HAL_PIXEL_FORMAT_YV12;
    descriptor.width = 640;
    descriptor.height = 480;
    descriptor.stride[0] = 640;
    descriptor.stride[1] = 320;

    // Create a buffer pool with default configuration
    BufferPool pool(allocator, descriptor);

    // Acquire a buffer from the pool
    GraphicBuffer* buf = pool.acquireBuffer();

    if (buf) {
        // Use the buffer...
        // ...

        // Release the buffer back to the pool
        pool.releaseBuffer(buf);
    }

    return 0;
}
```

This example demonstrates how to create a `BufferPool`, acquire a buffer, use it, and release it back to the pool.