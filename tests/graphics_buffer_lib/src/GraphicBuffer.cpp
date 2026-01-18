/**
 * @file GraphicBuffer.cpp
 * @brief Implementation of GraphicBuffer class
 */

#include "GraphicBuffer.h"
#include "IBufferAllocator.h"
#include "FenceManager.h"
#include <cstring>

namespace android {
namespace graphics {

std::atomic<uint64_t> GraphicBuffer::nextBufferId_{1};

GraphicBuffer::GraphicBuffer(
    const BufferDescriptor& descriptor,
    NativeHandle handle,
    IBufferAllocator* allocator
)
    : descriptor_(descriptor)
    , handle_(handle)
    , allocator_(allocator)
    , bufferId_(nextBufferId_.fetch_add(1))
{
}

GraphicBuffer::GraphicBuffer(GraphicBuffer&& other) noexcept
    : descriptor_(other.descriptor_)
    , handle_(other.handle_)
    , allocator_(other.allocator_)
    , mappedRegion_(other.mappedRegion_)
    , refCount_(other.refCount_.load())
    , bufferId_(other.bufferId_)
    , fenceManager_(other.fenceManager_)
    , acquireFenceFd_(other.acquireFenceFd_)
{
    other.handle_.fd = -1;
    other.allocator_ = nullptr;
    other.acquireFenceFd_ = -1;
}

GraphicBuffer::~GraphicBuffer() {
    if (mappedRegion_.isLocked()) {
        unlock();
    }
    
    if (allocator_ && handle_.isValid()) {
        allocator_->free(this);
    }
}

bool GraphicBuffer::lockForRead(MappedRegion& outRegion) {
    std::lock_guard<std::mutex> lock(lockMutex_);
    
    if (mappedRegion_.isLocked()) {
        return false;  // Already locked
    }
    
    // Wait for acquire fence
    if (acquireFenceFd_ >= 0) {
        waitAcquireFence(1000);
    }
    
    // Perform the lock (platform-specific)
    mappedRegion_.data = nullptr;  // Would be set by platform mapper
    mappedRegion_.size = descriptor_.calculateSize();
    mappedRegion_.lockMode = 1;  // Read
    
    outRegion = mappedRegion_;
    return true;
}

bool GraphicBuffer::lockForWrite(MappedRegion& outRegion) {
    std::lock_guard<std::mutex> lock(lockMutex_);
    
    if (mappedRegion_.isLocked()) {
        return false;
    }
    
    if (acquireFenceFd_ >= 0) {
        waitAcquireFence(1000);
    }
    
    mappedRegion_.data = nullptr;
    mappedRegion_.size = descriptor_.calculateSize();
    mappedRegion_.lockMode = 2;  // Write
    
    outRegion = mappedRegion_;
    return true;
}

bool GraphicBuffer::lockRegion(
    uint32_t x, uint32_t y,
    uint32_t width, uint32_t height,
    MappedRegion& outRegion
) {
    std::lock_guard<std::mutex> lock(lockMutex_);
    
    if (mappedRegion_.isLocked()) {
        return false;
    }
    
    // Validate region bounds
    if (x + width > descriptor_.width || y + height > descriptor_.height) {
        return false;
    }
    
    mappedRegion_.data = nullptr;
    mappedRegion_.size = width * height * 4;  // Simplified
    mappedRegion_.lockMode = 3;  // Region lock
    
    outRegion = mappedRegion_;
    return true;
}

bool GraphicBuffer::unlock() {
    std::lock_guard<std::mutex> lock(lockMutex_);
    
    if (!mappedRegion_.isLocked()) {
        return false;
    }
    
    // Platform-specific unlock
    mappedRegion_.data = nullptr;
    mappedRegion_.size = 0;
    mappedRegion_.lockMode = 0;
    
    return true;
}

NativeHandle GraphicBuffer::duplicateHandle() const {
    NativeHandle dup;
    dup.fd = handle_.fd;  // Would be actual dup() call
    dup.numFds = handle_.numFds;
    dup.numInts = handle_.numInts;
    std::memcpy(dup.data, handle_.data, sizeof(dup.data));
    return dup;
}

void GraphicBuffer::incRef() {
    refCount_.fetch_add(1, std::memory_order_relaxed);
}

bool GraphicBuffer::decRef() {
    int32_t prev = refCount_.fetch_sub(1, std::memory_order_acq_rel);
    return prev == 1;
}

int32_t GraphicBuffer::getRefCount() const {
    return refCount_.load(std::memory_order_relaxed);
}

void GraphicBuffer::setAcquireFence(FenceManager* fenceManager, int fenceFd) {
    fenceManager_ = fenceManager;
    acquireFenceFd_ = fenceFd;
}

bool GraphicBuffer::waitAcquireFence(uint32_t timeoutMs) {
    if (acquireFenceFd_ < 0) {
        return true;  // No fence to wait
    }
    
    // Platform-specific fence wait
    // In reality, would use sync_wait()
    acquireFenceFd_ = -1;
    return true;
}

// BufferDescriptor implementation
size_t BufferDescriptor::calculateSize() const {
    if (!isValid()) return 0;
    
    size_t bpp = 4;  // Default RGBA
    switch (format) {
        case PixelFormat::RGBA_8888:
        case PixelFormat::RGBX_8888:
        case PixelFormat::BGRA_8888:
            bpp = 4;
            break;
        case PixelFormat::RGB_888:
            bpp = 3;
            break;
        case PixelFormat::RGB_565:
            bpp = 2;
            break;
        case PixelFormat::NV21:
        case PixelFormat::NV12:
        case PixelFormat::YV12:
            // Y plane + UV plane (1.5 bytes per pixel)
            return stride * height * 3 / 2;
        default:
            bpp = 4;
    }
    
    return stride * height * bpp * layerCount;
}

bool BufferDescriptor::isValid() const {
    return width > 0 && height > 0 && format != PixelFormat::UNKNOWN;
}

std::string BufferDescriptor::toString() const {
    char buf[256];
    snprintf(buf, sizeof(buf), 
        "BufferDescriptor{%ux%u stride=%u format=%d usage=0x%llx layers=%u}",
        width, height, stride, static_cast<int>(format),
        static_cast<unsigned long long>(usage), layerCount);
    return buf;
}

// NativeHandle implementation
void NativeHandle::close() {
    if (fd >= 0) {
        // Would call ::close(fd)
        fd = -1;
    }
}

} // namespace graphics
} // namespace android
