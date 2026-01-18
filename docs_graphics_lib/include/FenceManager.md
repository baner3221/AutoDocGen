# FenceManager.h

---

| Property | Value |
|----------|-------|
| **Location** | `include\FenceManager.h` |
| **Lines** | 217 |
| **Classes** | 2 |
| **Functions** | 0 |
| **Last Updated** | 2026-01-18 13:28 |

---

## Quick Navigation

### Classes
- [android::graphics::Fence](#android-graphics-fence)
- [android::graphics::FenceManager](#android-graphics-fencemanager)

---

# FenceManager Documentation

## 1. Comprehensive Description (2-4 paragraphs)

The `FenceManager` class provides a comprehensive management solution for synchronization fences in graphics buffer operations. It abstracts the complexities of sync fences, allowing developers to manage and synchronize GPU/CPU operations efficiently. The class supports various fence states, such as unsignaled, signaled, error, and invalid, and offers methods to create, signal, wait on, and merge fences.

### Why does it exist? What problem does it solve?

The `FenceManager` addresses the need for robust synchronization in graphics buffer operations by providing a unified interface for managing sync fences. It simplifies the process of synchronizing GPU/CPU operations, reducing the risk of race conditions and ensuring that resources are managed correctly. The class also supports asynchronous wait operations, allowing developers to handle fence signals without blocking the main thread.

### How does it fit into the larger workflow?

The `FenceManager` is a critical component in the graphics buffer workflow, particularly in scenarios where multiple operations need to be synchronized. It provides a centralized point for managing fences, ensuring that all operations are properly synchronized and that resources are released correctly when they are no longer needed.

### Key algorithms or techniques used

- **Fence State Management**: The class uses an enumeration (`FenceState`) to track the state of each fence, allowing developers to easily determine the current status of a fence.
- **Fence Creation and Tracking**: The `createFence` method creates new fences and stores them in a list for later management. This ensures that all fences are properly tracked and can be accessed when needed.

## 2. Parameters (DETAILED for each)

### FenceManager::Fence

#### Constructor
- **Purpose**: Initializes a new fence.
- **Type Semantics**: `Fence` is an abstraction over sync fences, representing a synchronization primitive used to coordinate GPU/CPU operations.
- **Valid Values**: None.
- **Ownership**: The fence does not transfer ownership of the file descriptor. It takes ownership of the file descriptor passed to the constructor.
- **Nullability**: Can be null if the file descriptor is invalid.

#### Constructor (int fd)
- **Purpose**: Initializes a new fence from an existing file descriptor.
- **Type Semantics**: `Fence` is an abstraction over sync fences, representing a synchronization primitive used to coordinate GPU/CPU operations.
- **Valid Values**: The file descriptor must be valid and represent a sync fence.
- **Ownership**: The fence takes ownership of the file descriptor passed to the constructor.
- **Nullability**: Can be null if the file descriptor is invalid.

#### Move Constructor
- **Purpose**: Moves an existing fence to this instance.
- **Type Semantics**: `Fence` is an abstraction over sync fences, representing a synchronization primitive used to coordinate GPU/CPU operations.
- **Valid Values**: The source fence must be valid and not already moved.
- **Ownership**: The source fence is transferred to this instance. The source fence becomes invalid after the move.
- **Nullability**: Can be null if the source fence is invalid.

#### Destructor
- **Purpose**: Closes the file descriptor associated with the fence.
- **Type Semantics**: `Fence` is an abstraction over sync fences, representing a synchronization primitive used to coordinate GPU/CPU operations.
- **Valid Values**: The fence must be valid and not already closed.
- **Ownership**: The file descriptor is released when the fence is destroyed.
- **Nullability**: Can be null if the fence is invalid.

#### Signal
- **Purpose**: Waits for the fence to signal, with an optional timeout.
- **Type Semantics**: `bool` indicates whether the fence has signaled.
- **Valid Values**: The timeout can be set to `UINT32_MAX` for infinite wait or a specific duration in milliseconds.
- **Ownership**: None.
- **Nullability**: Can be null if the fence is invalid.

#### IsSignaled
- **Purpose**: Checks if the fence is already signaled without waiting.
- **Type Semantics**: `bool` indicates whether the fence has signaled.
- **Valid Values**: None.
- **Ownership**: None.
- **Nullability**: Can be null if the fence is invalid.

#### GetState
- **Purpose**: Retrieves the current state of the fence.
- **Type Semantics**: `FenceState` represents the current state of the fence (e.g., unsignaled, signaled).
- **Valid Values**: None.
- **Ownership**: None.
- **Nullability**: Can be null if the fence is invalid.

#### GetFd
- **Purpose**: Retrieves the file descriptor associated with the fence.
- **Type Semantics**: `int` represents the file descriptor of the sync fence.
- **Valid Values**: The file descriptor must be valid and represent a sync fence.
- **Ownership**: None.
- **Nullability**: Can be null if the fence is invalid.

#### Dup
- **Purpose**: Duplicates the file descriptor associated with the fence.
- **Type Semantics**: `int` represents the duplicated file descriptor (caller owns).
- **Valid Values**: The file descriptor must be valid and represent a sync fence.
- **Ownership**: The caller owns the duplicated file descriptor. The original file descriptor remains valid.
- **Nullability**: Can be null if the fence is invalid.

#### IsValid
- **Purpose**: Checks if the fence is valid.
- **Type Semantics**: `bool` indicates whether the fence is valid.
- **Valid Values**: None.
- **Ownership**: None.
- **Nullability**: Can be null if the fence is invalid.

#### CreateSignaled
- **Purpose**: Creates a signaled fence (no-op fence).
- **Type Semantics**: `Fence` represents the created fence.
- **Valid Values**: None.
- **Ownership**: The fence does not transfer ownership of the file descriptor. It takes ownership of the file descriptor passed to the constructor.
- **Nullability**: Can be null if the fence is invalid.

#### Merge
- **Purpose**: Merges multiple fences into one, signaling when all inputs signal.
- **Type Semantics**: `Fence` represents the merged fence.
- **Valid Values**: The input fences must be valid and not already merged.
- **Ownership**: The input fences are transferred to this instance. The input fences become invalid after the merge.
- **Nullability**: Can be null if any of the input fences are invalid.

#### Merge (Fence&& a, Fence&& b)
- **Purpose**: Merges two fences into one, signaling when both inputs signal.
- **Type Semantics**: `Fence` represents the merged fence.
- **Valid Values**: The input fences must be valid and not already merged.
- **Ownership**: The input fences are transferred to this instance. The input fences become invalid after the merge.
- **Nullability**: Can be null if any of the input fences are invalid.

#### GetSignalTime
- **Purpose**: Retrieves the signal time (if signaled) in nanoseconds.
- **Type Semantics**: `int64_t` represents the signal time in nanoseconds.
- **Valid Values**: The fence must be signaled to return a valid value. If not signaled, returns -1.
- **Ownership**: None.
- **Nullability**: Can be null if the fence is invalid.

### FenceManager

#### Constructor
- **Purpose**: Initializes a new `FenceManager`.
- **Type Semantics**: `FenceManager` manages synchronization fences for graphics buffer operations.
- **Valid Values**: None.
- **Ownership**: The `FenceManager` does not transfer ownership of any resources. It manages its own internal state.
- **Nullability**: Can be null if the `FenceManager` is invalid.

#### Destructor
- **Purpose**: Cleans up all active fences and releases resources.
- **Type Semantics**: `FenceManager` manages synchronization fences for graphics buffer operations.
- **Valid Values**: None.
- **Ownership**: The `FenceManager` does not transfer ownership of any resources. It manages its own internal state.
- **Nullability**: Can be null if the `FenceManager` is invalid.

#### CreateFence
- **Purpose**: Creates a new timeline fence with an optional debug name.
- **Type Semantics**: `Fence` represents the created fence.
- **Valid Values**: The debug name can be any string. If not provided, a default name is used.
- **Ownership**: The fence does not transfer ownership of the file descriptor. It takes ownership of the file descriptor passed to the constructor.
- **Nullability**: Can be null if the fence is invalid.

#### SignalFence
- **Purpose**: Signals a fence (for CPU-signaled fences).
- **Type Semantics**: `bool` indicates whether the signal was successful.
- **Valid Values**: The fence must be valid and not already signaled.
- **Ownership**: None.
- **Nullability**: Can be null if the fence is invalid.

#### WaitAsync
- **Purpose**: Waits for a fence asynchronously, calling a callback when the fence signals.
- **Type Semantics**: `void` indicates that the operation completes asynchronously.
- **Valid Values**: The fence must be valid and not already signaled. The callback must be non-null.
- **Ownership**: None.
- **Nullability**: Can be null if the fence is invalid.

#### WaitMultiple
- **Purpose**: Waits for multiple fences, either waiting for all or any to signal.
- **Type Semantics**: `int` represents the index of the signaled fence (or -1 on timeout).
- **Valid Values**: The fences must be valid and not already signaled. The waitAll parameter determines whether to wait for all or any fences to signal. The timeout can be set to `UINT32_MAX` for infinite wait.
- **Ownership**: None.
- **Nullability**: Can be null if any of the input