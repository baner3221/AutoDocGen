/**
 * @file GraphicsBuffer.h
 * @brief Unified include for the Android Graphics Buffer Library
 * 
 * This header includes all public APIs for the graphics buffer system.
 * 
 * @example Basic Usage
 * @code
 * #include <GraphicsBuffer.h>
 * 
 * using namespace android::graphics;
 * 
 * // Create allocator
 * auto allocator = AllocatorFactory::createDefault();
 * 
 * // Create buffer pool for camera preview
 * BufferDescriptor desc{1920, 1080, 0, PixelFormat::NV21,
 *     BufferUsage::CAMERA_OUTPUT | BufferUsage::GPU_TEXTURE};
 * BufferPool pool(allocator, desc);
 * 
 * // Acquire and use buffers
 * GraphicBuffer* buf = pool.acquireBuffer();
 * BufferLockGuard guard(buf, BufferLockGuard::LockMode::Write);
 * // Fill buffer...
 * guard.unlock();
 * pool.releaseBuffer(buf);
 * @endcode
 */

#pragma once

// Core types
#include "BufferTypes.h"

// Allocation interfaces
#include "IBufferAllocator.h"
#include "GrallocAllocator.h"

// Buffer classes
#include "GraphicBuffer.h"
#include "BufferPool.h"
#include "BufferMapper.h"
#include "BufferCache.h"

// Camera integration
#include "CameraBufferManager.h"

// Synchronization
#include "FenceManager.h"

namespace android {
namespace graphics {

/**
 * @brief Library version information
 */
struct Version {
    static constexpr int MAJOR = 1;
    static constexpr int MINOR = 0;
    static constexpr int PATCH = 0;
    static constexpr const char* STRING = "1.0.0";
};

/**
 * @brief Initialize the graphics buffer library
 * @return True on success
 */
bool initialize();

/**
 * @brief Shutdown and cleanup
 */
void shutdown();

/**
 * @brief Get library version string
 */
const char* getVersionString();

} // namespace graphics
} // namespace android
