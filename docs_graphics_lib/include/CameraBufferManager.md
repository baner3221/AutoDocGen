# CameraBufferManager.h

---

| Property | Value |
|----------|-------|
| **Location** | `include\CameraBufferManager.h` |
| **Lines** | 240 |
| **Classes** | 2 |
| **Functions** | 0 |
| **Last Updated** | 2026-01-18 13:28 |

---

## Quick Navigation

### Classes
- [android::graphics::StreamConfiguration](#android-graphics-streamconfiguration)
- [android::graphics::CameraBufferManager](#android-graphics-camerabuffermanager)

---

## Documentation for `CameraBufferManager`

### 1. Comprehensive Description (2-4 paragraphs)

`CameraBufferManager` is a specialized buffer management layer designed to handle camera-specific buffer allocation and streaming requirements. It interfaces with the Android camera framework to provide optimized buffer allocation and streaming for camera capture pipelines. This class manages multiple camera streams, supporting various types of buffers such as preview, video, stills, raw data, and reprocessing.

### 2. Parameters (DETAILED for each)

#### `CameraBufferManager(std::shared_ptr<IBufferAllocator> allocator)`

- **Purpose**: Initializes a new instance of `CameraBufferManager` using the provided buffer allocator.
- **Type Semantics**: `std::shared_ptr<IBufferAllocator>` represents a shared pointer to an interface that allocates buffers for camera streams.
- **Valid Values**: The allocator must be valid and capable of allocating memory for camera buffers.
- **Ownership**: The allocator is owned by the caller and passed as a shared pointer. It remains valid throughout the lifetime of `CameraBufferManager`.
- **Nullability**: The allocator cannot be null.

#### `CameraBufferManager(std::shared_ptr<IBufferAllocator> allocator, std::shared_ptr<FenceManager> fenceManager)`

- **Purpose**: Initializes a new instance of `CameraBufferManager` using the provided buffer allocator and fence manager.
- **Type Semantics**: `std::shared_ptr<IBufferAllocator>` represents a shared pointer to an interface that allocates buffers for camera streams, while `std::shared_ptr<FenceManager>` represents a shared pointer to an interface that manages fences used for synchronization between different system components.
- **Valid Values**: Both the allocator and fence manager must be valid and capable of performing their respective tasks.
- **Ownership**: The allocator is owned by the caller and passed as a shared pointer. It remains valid throughout the lifetime of `CameraBufferManager`. The fence manager is also owned by the caller and passed as a shared pointer. It remains valid throughout the lifetime of `CameraBufferManager`.
- **Nullability**: Neither the allocator nor the fence manager can be null.

#### `~CameraBufferManager() override`

- **Purpose**: Destructor for `CameraBufferManager` that cleans up any resources held.
- **Type Semantics**: No parameters are required.
- **Valid Values**: The destructor does not accept any values.
- **Ownership**: No ownership is transferred or modified.
- **Nullability**: There are no null pointers to manage.

#### `configureStream(const StreamConfiguration& config)`

- **Purpose**: Configures a new stream based on the provided configuration.
- **Type Semantics**: `const StreamConfiguration&` represents a reference to a constant stream configuration structure that specifies details about the stream, such as its type, buffer descriptor, pool configuration, rotation, and use case hint.
- **Valid Values**: The configuration must be valid and contain all necessary information for configuring a camera stream. The buffer descriptor should specify the dimensions, format, and other properties of the buffers required by the stream. The pool configuration should define how many buffers are needed and their characteristics.
- **Ownership**: The configuration is borrowed from the caller and not modified.
- **Nullability**: The configuration cannot be null.

#### `reconfigureStream(uint32_t streamId, const StreamConfiguration& newConfig)`

- **Purpose**: Reconfigures an existing stream with a new configuration.
- **Type Semantics**: `uint32_t` represents the ID of the stream to reconfigure, and `const StreamConfiguration&` represents a reference to a constant stream configuration structure that specifies the new details for the stream.
- **Valid Values**: The stream ID must be valid (i.e., it should correspond to an existing stream). The new configuration must be valid and contain all necessary information for configuring the camera stream. The buffer descriptor should specify the dimensions, format, and other properties of the buffers required by the stream. The pool configuration should define how many buffers are needed and their characteristics.
- **Ownership**: The stream ID is borrowed from the caller and not modified. The new configuration is borrowed from the caller and not modified.
- **Nullability**: Neither the stream ID nor the new configuration can be null.

#### `removeStream(uint32_t streamId, bool waitForBuffers)`

- **Purpose**: Removes a stream and optionally waits for all buffers to be returned before completing the operation.
- **Type Semantics**: `uint32_t` represents the ID of the stream to remove, and `bool` represents whether to wait for buffers to be returned.
- **Valid Values**: The stream ID must be valid (i.e., it should correspond to an existing stream). The `waitForBuffers` parameter can be either true or false.
- **Ownership**: The stream ID is borrowed from the caller and not modified. The `waitForBuffers` parameter is passed as a boolean value.
- **Nullability**: Neither the stream ID nor the `waitForBuffers` parameter can be null.

#### `dequeueBuffer(uint32_t streamId, int* outFenceFd)`

- **Purpose**: Dequeues a buffer for a specified stream from the producer side.
- **Type Semantics**: `uint32_t` represents the ID of the target stream, and `int*` is a pointer to an integer where the acquire fence file descriptor will be stored if available.
- **Valid Values**: The stream ID must be valid (i.e., it should correspond to an existing stream). The `outFenceFd` parameter can be null or point to a location where the acquire fence file descriptor will be written.
- **Ownership**: The stream ID is borrowed from the caller and not modified. The `outFenceFd` parameter is passed as a pointer to an integer, which may be null.
- **Nullability**: Neither the stream ID nor the `outFenceFd` parameter can be null.

#### `queueBuffer(uint32_t streamId, GraphicBuffer* buffer, int releaseFenceFd)`

- **Purpose**: Queues a filled buffer for consumption by the consumer side.
- **Type Semantics**: `uint32_t` represents the ID of the target stream, `GraphicBuffer*` is a pointer to the buffer to queue, and `int` is the release fence file descriptor.
- **Valid Values**: The stream ID must be valid (i.e., it should correspond to an existing stream). The buffer must be valid and contain data. The `releaseFenceFd` can be null or point to a location where the release fence file descriptor will be written.
- **Ownership**: The stream ID is borrowed from the caller and not modified. The buffer is transferred to this method, and ownership is passed to it. The `releaseFenceFd` parameter is passed as an integer, which may be null.
- **Nullability**: Neither the stream ID nor the `releaseFenceFd` parameter can be null.

#### `acquireBuffer(uint32_t streamId, int* outFenceFd)`

- **Purpose**: Acquires a buffer for consumption by the consumer side.
- **Type Semantics**: `uint32_t` represents the ID of the source stream, and `int*` is a pointer to an integer where the acquire fence file descriptor will be stored if available.
- **Valid Values**: The stream ID must be valid (i.e., it should correspond to an existing stream). The `outFenceFd` parameter can be null or point to a location where the acquire fence file descriptor will be written.
- **Ownership**: The stream ID is borrowed from the caller and not modified. The `outFenceFd` parameter is passed as a pointer to an integer, which may be null.
- **Nullability**: Neither the stream ID nor the `outFenceFd` parameter can be null.

#### `releaseBuffer(uint32_t streamId, GraphicBuffer* buffer, int releaseFenceFd)`

- **Purpose**: Releases a consumed buffer back to the producer side.
- **Type Semantics**: `uint32_t` represents the ID of the source stream, `GraphicBuffer*` is a pointer to the buffer to release, and `int` is the release fence file descriptor.
- **Valid Values**: The stream ID must be valid (i.e., it should correspond to an existing stream). The buffer must be valid and contain data. The `releaseFenceFd` can be null or point to a location where the release fence file descriptor will be written.
- **Ownership**: The stream ID is borrowed from the caller and not modified. The buffer is transferred to this method, and ownership is passed to it. The `releaseFenceFd` parameter is passed as an integer, which may be null.
- **Nullability**: Neither the stream ID nor the `releaseFenceFd` parameter can be null.

#### `setBufferCallback(BufferCallback callback)`

- **Purpose**: Sets a callback function for buffer availability notifications.
- **Type Semantics**: `BufferCallback` is a function object that takes two parameters: the stream ID and a pointer to the acquired buffer. The function should not modify the buffer or any of its contents.
- **Valid Values**: The callback function must be valid and callable with the specified signature.
- **Ownership**: The callback function is passed as a copy, and ownership is transferred to this method.
- **Nullability**: The callback function can be null.

#### `setErrorCallback(ErrorCallback callback)`

- **Purpose**: Sets a callback function for error notifications.
- **Type Semantics**: `ErrorCallback` is a function object that takes two parameters: the stream ID and an allocation status. The function should not modify any of its contents.
- **Valid Values**: The callback function must be valid and callable with the specified signature.
- **Ownership**: The callback function is passed as a copy, and ownership is transferred to this method.
- **Nullability**: The callback function can be null