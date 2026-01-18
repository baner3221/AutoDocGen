/**
 * @file BufferMapper.h
 * @brief Utility class for simplified buffer CPU access
 * 
 * Provides RAII-style buffer locking and high-level access patterns.
 */

#pragma once

#include "BufferTypes.h"
#include "GraphicBuffer.h"
#include <memory>
#include <functional>

namespace android {
namespace graphics {

/**
 * @brief RAII lock guard for buffer CPU access
 * 
 * Automatically locks buffer on construction and unlocks on destruction.
 * 
 * @code
 * {
 *     BufferLockGuard guard(buffer, BufferLockGuard::LockMode::ReadWrite);
 *     if (guard) {
 *         uint8_t* data = guard.getData<uint8_t>();
 *         // Modify data...
 *     }
 * } // Automatically unlocked here
 * @endcode
 */
class BufferLockGuard {
public:
    enum class LockMode {
        Read,
        Write,
        ReadWrite
    };
    
    /**
     * @brief Lock entire buffer
     * @param buffer Buffer to lock
     * @param mode Access mode
     */
    BufferLockGuard(GraphicBuffer* buffer, LockMode mode);
    
    /**
     * @brief Lock a region of the buffer
     */
    BufferLockGuard(
        GraphicBuffer* buffer,
        LockMode mode,
        uint32_t x, uint32_t y,
        uint32_t width, uint32_t height
    );
    
    /**
     * @brief Destructor - unlocks buffer
     */
    ~BufferLockGuard();
    
    // Non-copyable
    BufferLockGuard(const BufferLockGuard&) = delete;
    BufferLockGuard& operator=(const BufferLockGuard&) = delete;
    
    // Move-only
    BufferLockGuard(BufferLockGuard&& other) noexcept;
    
    /**
     * @brief Check if lock succeeded
     */
    explicit operator bool() const { return locked_; }
    
    /**
     * @brief Get typed pointer to buffer data
     */
    template<typename T>
    T* getData() { return static_cast<T*>(region_.data); }
    
    template<typename T>
    const T* getData() const { return static_cast<const T*>(region_.data); }
    
    /**
     * @brief Get raw data pointer
     */
    void* getRawData() { return region_.data; }
    
    /**
     * @brief Get size of mapped region
     */
    size_t getSize() const { return region_.size; }
    
    /**
     * @brief Manually unlock before destruction
     */
    void unlock();

private:
    GraphicBuffer* buffer_;
    MappedRegion region_;
    bool locked_;
};

/**
 * @brief High-level buffer mapping utilities
 * 
 * Provides convenience methods for common buffer access patterns.
 */
class BufferMapper {
public:
    /**
     * @brief Copy data from buffer to CPU memory
     * @param buffer Source buffer
     * @param dest Destination memory
     * @param size Maximum bytes to copy
     * @return Bytes copied, or 0 on failure
     */
    static size_t copyFromBuffer(
        GraphicBuffer* buffer,
        void* dest,
        size_t size
    );
    
    /**
     * @brief Copy data from CPU memory to buffer
     * @param buffer Destination buffer
     * @param src Source memory
     * @param size Bytes to copy
     * @return True on success
     */
    static bool copyToBuffer(
        GraphicBuffer* buffer,
        const void* src,
        size_t size
    );
    
    /**
     * @brief Fill buffer with a constant value
     * @param buffer Buffer to fill
     * @param value Value to fill with
     * @return True on success
     */
    static bool fillBuffer(GraphicBuffer* buffer, uint8_t value);
    
    /**
     * @brief Process buffer data with a callback
     * 
     * @code
     * BufferMapper::processBuffer(buffer, [](void* data, size_t size) {
     *     // Process data...
     * });
     * @endcode
     */
    static bool processBuffer(
        GraphicBuffer* buffer,
        std::function<void(void* data, size_t size)> processor
    );
    
    /**
     * @brief Calculate row stride for a format
     * @param format Pixel format
     * @param width Image width in pixels
     * @return Stride in bytes
     */
    static uint32_t calculateStride(PixelFormat format, uint32_t width);
    
    /**
     * @brief Get bytes per pixel for a format
     */
    static uint32_t getBytesPerPixel(PixelFormat format);
    
    /**
     * @brief Check if format is YUV-based
     */
    static bool isYuvFormat(PixelFormat format);
    
    /**
     * @brief Check if format is compressed
     */
    static bool isCompressedFormat(PixelFormat format);
};

} // namespace graphics
} // namespace android
