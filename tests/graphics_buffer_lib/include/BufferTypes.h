/**
 * @file BufferTypes.h
 * @brief Core type definitions for the Android Graphics Buffer Library
 * 
 * This header defines fundamental types, enums, and structures used
 * throughout the graphics buffer management system.
 */

#pragma once

#include <cstdint>
#include <cstddef>
#include <string>

namespace android {
namespace graphics {

/**
 * @brief Pixel format enumeration for buffer allocation
 * 
 * Matches Android HAL pixel formats for compatibility with
 * camera framework and display subsystems.
 */
enum class PixelFormat : uint32_t {
    UNKNOWN = 0,
    RGBA_8888 = 1,
    RGBX_8888 = 2,
    RGB_888 = 3,
    RGB_565 = 4,
    BGRA_8888 = 5,
    YV12 = 842094169,          // YCrCb 4:2:0 Planar
    NV21 = 17,                  // YCrCb 4:2:0 Semi-Planar
    NV12 = 35,                  // YCbCr 4:2:0 Semi-Planar
    RAW10 = 37,                 // Raw Bayer 10-bit
    RAW12 = 38,                 // Raw Bayer 12-bit
    RAW16 = 32,                 // Raw Bayer 16-bit
    BLOB = 33,                  // Arbitrary binary blob
    IMPLEMENTATION_DEFINED = 34 // Platform-specific format
};

/**
 * @brief Buffer usage flags (can be combined with bitwise OR)
 */
enum class BufferUsage : uint64_t {
    NONE = 0,
    CPU_READ_RARELY = 1ULL << 0,
    CPU_READ_OFTEN = 1ULL << 1,
    CPU_WRITE_RARELY = 1ULL << 2,
    CPU_WRITE_OFTEN = 1ULL << 3,
    GPU_TEXTURE = 1ULL << 8,
    GPU_RENDER_TARGET = 1ULL << 9,
    COMPOSER_OVERLAY = 1ULL << 11,
    CAMERA_INPUT = 1ULL << 16,
    CAMERA_OUTPUT = 1ULL << 17,
    VIDEO_ENCODER = 1ULL << 20,
    VIDEO_DECODER = 1ULL << 21,
    PROTECTED = 1ULL << 30,
    SENSOR_DIRECT_DATA = 1ULL << 35
};

inline BufferUsage operator|(BufferUsage a, BufferUsage b) {
    return static_cast<BufferUsage>(static_cast<uint64_t>(a) | static_cast<uint64_t>(b));
}

inline BufferUsage operator&(BufferUsage a, BufferUsage b) {
    return static_cast<BufferUsage>(static_cast<uint64_t>(a) & static_cast<uint64_t>(b));
}

/**
 * @brief Buffer allocation status codes
 */
enum class AllocationStatus {
    SUCCESS = 0,
    ERROR_NO_MEMORY,
    ERROR_INVALID_DIMENSIONS,
    ERROR_UNSUPPORTED_FORMAT,
    ERROR_GRALLOC_FAILURE,
    ERROR_DEVICE_LOST,
    ERROR_PERMISSION_DENIED
};

/**
 * @brief Describes the geometry and format of a buffer
 */
struct BufferDescriptor {
    uint32_t width = 0;
    uint32_t height = 0;
    uint32_t stride = 0;
    PixelFormat format = PixelFormat::UNKNOWN;
    BufferUsage usage = BufferUsage::NONE;
    uint32_t layerCount = 1;
    
    size_t calculateSize() const;
    bool isValid() const;
    std::string toString() const;
};

/**
 * @brief Native handle wrapper for gralloc buffers
 */
struct NativeHandle {
    int fd = -1;
    int numFds = 0;
    int numInts = 0;
    int data[64] = {0};
    
    bool isValid() const { return fd >= 0; }
    void close();
};

/**
 * @brief Memory region for CPU-side buffer access
 */
struct MappedRegion {
    void* data = nullptr;
    size_t size = 0;
    int lockMode = 0;
    
    bool isLocked() const { return data != nullptr; }
};

/**
 * @brief Statistics for buffer pool monitoring
 */
struct PoolStatistics {
    size_t totalBuffers = 0;
    size_t freeBuffers = 0;
    size_t allocatedBytes = 0;
    size_t peakAllocatedBytes = 0;
    uint64_t allocationCount = 0;
    uint64_t reuseCount = 0;
    double hitRate = 0.0;
};

} // namespace graphics
} // namespace android
