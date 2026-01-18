# BufferTypes.h

---

| Property | Value |
|----------|-------|
| **Location** | `include\BufferTypes.h` |
| **Lines** | 136 |
| **Classes** | 4 |
| **Functions** | 2 |
| **Last Updated** | 2026-01-18 20:07 |

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
The `BufferTypes.h` file defines enumerations and flags used to manage pixel formats and buffer usage in the Android graphics buffer library. The `PixelFormat` enumeration maps Android HAL pixel formats to a more readable format, facilitating compatibility with camera and display subsystems. The `BufferUsage` enum provides flags that can be combined using bitwise OR to specify how buffers are intended to be used, such as CPU read/write operations or GPU rendering targets.

### 2. Parameters (DETAILED for each)
#### PixelFormat
- **Purpose**: Defines the pixel format of a buffer.
- **Type Semantics**: An enumeration type that represents different pixel formats.
- **Valid Values**: A set of predefined values representing various Android HAL pixel formats, such as RGBA_8888, RGBX_8888, and YV12.
- **Ownership**: The enum values are static constants and do not own any memory.
- **Nullability**: Not applicable; the enum values are fixed.

#### BufferUsage
- **Purpose**: Defines flags that specify how a buffer is intended to be used.
- **Type Semantics**: An enumeration type that represents different usage patterns for buffers.
- **Valid Values**: A set of predefined bit flags representing various usage patterns, such as CPU_READ_RARELY and GPU_TEXTURE.
- **Ownership**: The enum values are static constants and do not own any memory.
- **Nullability**: Not applicable; the enum values are fixed.

### 3. Return Value
The function does not return a value.

### 4. Dependencies Cross-Reference
No external classes or functions are used in this file.

### 5. Side Effects
- No state modifications are made.
- No locks are acquired or released.
- No I/O operations are performed.
- No signals/events are emitted.

### 6. Usage Context
This file is typically included by other parts of the graphics buffer library to define pixel formats and buffer usage flags for buffer allocation and management.

### 7. Related Functions
| Relationship Type | Function Name | Description |
|-------------------|--------------|-------------|
| Enumerations      | PixelFormat   | Defines pixel formats. |
| Enumerations      | BufferUsage    | Defines buffer usage flags. |

### 8. Code Example

```cpp
// Example of using the BufferTypes.h file to define a buffer with specific pixel format and usage flags.
#include "BufferTypes.h"

int main() {
    // Define a buffer with RGBA_8888 pixel format and GPU_TEXTURE and CPU_READ_OFTEN usage flags.
    android::graphics::PixelFormat pixelFormat = android::graphics::PixelFormat::RGBA_8888;
    android::graphics::BufferUsage bufferUsage = android::graphics::BufferUsage::GPU_TEXTURE | android::graphics::BufferUsage::CPU_READ_OFTEN;

    // Use the defined pixel format and usage flags to allocate a buffer.
    // Buffer allocation logic would be implemented here.

    return 0;
}
```

This example demonstrates how to use the `PixelFormat` and `BufferUsage` enums to define a buffer with specific properties, which can then be used for further processing or rendering operations.

## Documentation for `BufferDescriptor`

### Comprehensive Description (2-4 paragraphs)
The `BufferDescriptor` struct in the `android::graphics` namespace is designed to encapsulate metadata about a graphics buffer, such as its dimensions, format, and usage flags. This structure is crucial for managing and allocating buffers efficiently within the Android system, ensuring that they are correctly configured for various rendering tasks.

### Parameters (DETAILED for each)
- **width**: 
  - **Purpose**: Specifies the width of the buffer in pixels.
  - **Type Semantics**: An unsigned integer representing the number of pixels along the horizontal axis.
  - **Valid Values**: Any non-negative integer.
  - **Ownership**: The value is owned by the `BufferDescriptor` instance.
  - **Nullability**: Not applicable.

- **height**: 
  - **Purpose**: Specifies the height of the buffer in pixels.
  - **Type Semantics**: An unsigned integer representing the number of pixels along the vertical axis.
  - **Valid Values**: Any non-negative integer.
  - **Ownership**: The value is owned by the `BufferDescriptor` instance.
  - **Nullability**: Not applicable.

- **stride**: 
  - **Purpose**: Defines the byte offset between consecutive rows in the buffer. This is particularly useful for buffers with a non-standard pixel format or when multiple layers are involved.
  - **Type Semantics**: An unsigned integer representing the number of bytes between the start of one row and the next.
  - **Valid Values**: Any positive integer, typically equal to `width * bytesPerPixel`, where `bytesPerPixel` is determined by the buffer's format.
  - **Ownership**: The value is owned by the `BufferDescriptor` instance.
  - **Nullability**: Not applicable.

- **format**: 
  - **Purpose**: Specifies the pixel format of the buffer, which determines how pixels are stored and interpreted.
  - **Type Semantics**: An enumeration (`PixelFormat`) representing the format type.
  - **Valid Values**: A set of predefined values such as `UNKNOWN`, `RGBA_8888`, `RGB_565`, etc. Each value corresponds to a specific color depth and layout.
  - **Ownership**: The value is owned by the `BufferDescriptor` instance.
  - **Nullability**: Not applicable.

- **usage**: 
  - **Purpose**: Indicates how the buffer will be used, such as for rendering or video processing.
  - **Type Semantics**: An enumeration (`BufferUsage`) representing the usage flags.
  - **Valid Values**: A set of predefined values such as `NONE`, `RENDERABLE`, `VIDEO_PROCESSOR`, etc. Each value indicates specific capabilities and intended use cases.
  - **Ownership**: The value is owned by the `BufferDescriptor` instance.
  - **Nullability**: Not applicable.

- **layerCount**: 
  - **Purpose**: Specifies the number of layers in a buffer, which is useful for multi-layered graphics operations.
  - **Type Semantics**: An unsigned integer representing the number of layers.
  - **Valid Values**: Any positive integer, typically 1 or more.
  - **Ownership**: The value is owned by the `BufferDescriptor` instance.
  - **Nullability**: Not applicable.

### Return Value
- **Purpose**: Returns a size_t representing the total size of the buffer in bytes based on its dimensions and format.
- **All Possible Return States**: A valid non-negative integer representing the buffer size.
- **Error Conditions and How They're Indicated**: No error conditions are expected, as the calculation is straightforward.
- **Ownership of Returned Objects**: The return value is a simple integer and does not transfer ownership.

### Dependencies Cross-Reference
- `PixelFormat`: Used to determine the byte per pixel for calculating buffer size.
- `BufferUsage`: Used to validate usage flags during buffer allocation.

### Side Effects
- State modifications: Updates the internal state of the `BufferDescriptor` instance with new values.
- Locks acquired/released: No locks are involved in this operation.
- I/O operations: No I/O operations are performed.
- Signals/events emitted: No signals or events are emitted.

### Usage Context
This struct is typically used during buffer allocation and configuration within the Android graphics subsystem. It provides a standardized way to describe buffer requirements, which helps in managing resources efficiently and ensuring compatibility across different rendering pipelines.

### Related Functions
| Relationship Type | Function Name | Description |
|------------------|--------------|-------------|
| Member           | calculateSize() | Calculates the total size of the buffer based on its dimensions and format. |
| Member           | isValid() const | Checks if the buffer descriptor is valid by ensuring all fields have non-negative values. |
| Member           | toString() const | Converts the buffer descriptor to a string representation for debugging purposes. |

### Code Example
```cpp
BufferDescriptor desc;
desc.width = 1920;
desc.height = 1080;
desc.format = PixelFormat::RGBA_8888;
desc.usage = BufferUsage::RENDERABLE;

size_t bufferSize = desc.calculateSize();
if (bufferSize > 0) {
    // Allocate buffer memory using the calculated size
} else {
    ALOGE("Invalid buffer descriptor");
}
```

## Documentation for `NativeHandle`

### Comprehensive Description (2-4 paragraphs)
The `NativeHandle` struct in the `android::graphics` namespace is a wrapper around native graphics handles, such as file descriptors or shared memory objects. This structure is used to manage and access native resources efficiently within the Android system.

### Parameters (DETAILED for each)
- **fd**: 
  - **Purpose**: Represents the file descriptor of the native resource.
  - **Type Semantics**: An integer representing a file descriptor.
  - **Valid Values**: A valid file descriptor number, typically non-negative.
  - **Ownership**: The value is owned by the `NativeHandle` instance.
  - **Nullability**: Can be null (e.g., when the handle is not yet initialized).

- **numFds**: 
  - **Purpose**: Specifies the number of additional file descriptors associated with the native resource.
  - **Type Semantics**: An integer representing the count of additional file descriptors.
  - **Valid Values**: Any non-negative integer, typically 0 or more.
  - **Ownership**: The value is owned by the `NativeHandle` instance.
  - **Nullability**: Can be null (e.g., when no additional file descriptors are used).

- **numInts**: 
  - **Purpose**: Specifies the number of integer values associated with the native resource.
  - **Type Semantics**: An integer representing the count of integer values.
  - **Valid Values**: Any non-negative integer, typically 0 or more.
  - **Ownership**: The value is owned by the `NativeHandle` instance.
  - **Nullability**: Can be null (e.g., when no additional integer values are used).

- **data**: 
  - **Purpose**: An array of integers to store additional data associated with the native resource.
  - **Type Semantics**: An array of integers.
  - **Valid Values**: A set of integer values, typically used for passing additional metadata or configuration parameters.
  - **Ownership**: The array is owned by the `NativeHandle` instance.
  - **Nullability**: Can be null (e.g., when no additional data is needed).

### Return Value
- **Purpose**: Returns a boolean indicating whether the native handle is valid, i.e., if the file descriptor is non-negative.
- **All Possible Return States**: A boolean value (`true` or `false`).
- **Error Conditions and How They're Indicated**: No error conditions are expected, as the validity check is straightforward.
- **Ownership of Returned Objects**: The return value is a simple boolean and does not transfer ownership.

### Dependencies Cross-Reference
No external classes/functions are used in this context.

### Side Effects
- State modifications: Updates the internal state of the `NativeHandle` instance with new values.
- Locks acquired/released: No locks are involved in this operation.
- I/O operations: No I/O operations are performed.
- Signals/events emitted: No signals or events are emitted.

### Usage Context
This struct is typically used during buffer allocation and configuration within the Android graphics subsystem. It provides a standardized way to manage native resources, which helps in ensuring efficient resource management and compatibility across different rendering pipelines.

### Related Functions
No related functions are defined for this struct.

### Code Example
```cpp
NativeHandle handle;
handle.fd = open("/dev/graphics/fb0", O_RDWR);
if (handle.fd >= 0) {
    // Use the native handle for buffer operations
} else {
    ALOGE("Failed to open framebuffer device");
}
```

## Documentation for `MappedRegion`

### Comprehensive Description (2-4 paragraphs)
The `MappedRegion` struct in the `android::graphics` namespace is used to represent a memory region that has been mapped into the process's address space. This structure is crucial for accessing buffer data directly on the CPU.

### Parameters (DETAILED for each)
- **data**: 
  - **Purpose**: Points to the start of the mapped memory region.
  - **Type Semantics**: A pointer to a block of memory.
  - **Valid Values**: A valid memory address, typically obtained from a buffer mapping operation.
  - **Ownership**: The pointer is owned by the `MappedRegion` instance.
  - **Nullability**: Can be null (e.g., when the region is not yet mapped).

- **size**: 
  - **Purpose**: Specifies the size of the mapped memory region in bytes.
  - **Type Semantics**: A size_t representing the number of bytes.
  - **Valid Values**: Any non-negative integer, typically equal to the buffer's size.
  - **Ownership**: The value is owned by the