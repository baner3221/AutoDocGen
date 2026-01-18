/**
 * @file GrallocAllocator.cpp
 * @brief Implementation of GrallocAllocator class
 */

#include "GrallocAllocator.h"
#include "GraphicBuffer.h"
#include "BufferCache.h"
#include <thread>
#include <sstream>

namespace android {
namespace graphics {

GrallocAllocator::GrallocAllocator()
    : GrallocAllocator(GrallocVersion::GRALLOC_4_0)  // Auto-detect would go here
{
}

GrallocAllocator::GrallocAllocator(GrallocVersion version)
    : version_(version)
    , mapper_(std::make_unique<GrallocMapper>(version))
    , cache_(std::make_unique<BufferCache>(128))
{
    initializeHal();
}

GrallocAllocator::~GrallocAllocator() {
    shutdownHal();
}

AllocationStatus GrallocAllocator::allocate(
    const BufferDescriptor& descriptor,
    std::unique_ptr<GraphicBuffer>& outBuffer
) {
    if (!descriptor.isValid()) {
        return AllocationStatus::ERROR_INVALID_DIMENSIONS;
    }
    
    if (!isFormatSupported(descriptor.format, descriptor.usage)) {
        return AllocationStatus::ERROR_UNSUPPORTED_FORMAT;
    }
    
    std::lock_guard<std::mutex> lock(allocMutex_);
    
    NativeHandle handle;
    AllocationStatus status = allocateInternal(descriptor, handle);
    
    if (status != AllocationStatus::SUCCESS) {
        return status;
    }
    
    outBuffer = std::make_unique<GraphicBuffer>(descriptor, handle, this);
    activeBuffers_[outBuffer->getBufferId()] = outBuffer.get();
    
    // Cache the entry
    BufferCacheEntry entry;
    entry.bufferId = outBuffer->getBufferId();
    entry.descriptor = descriptor;
    entry.handle = handle;
    cache_->insert(entry);
    
    return AllocationStatus::SUCCESS;
}

void GrallocAllocator::allocateAsync(
    const BufferDescriptor& descriptor,
    AllocationCallback callback
) {
    // Launch async allocation on worker thread
    std::thread([this, descriptor, callback]() {
        std::unique_ptr<GraphicBuffer> buffer;
        AllocationStatus status = allocate(descriptor, buffer);
        callback(status, buffer.release());
    }).detach();
}

void GrallocAllocator::free(GraphicBuffer* buffer) {
    if (!buffer) return;
    
    std::lock_guard<std::mutex> lock(allocMutex_);
    
    uint64_t id = buffer->getBufferId();
    
    // Remove from active buffers
    activeBuffers_.erase(id);
    
    // Invalidate cache
    cache_->invalidate(id);
    
    // Platform-specific free would happen here
    // gralloc->freeBuffer(buffer->getNativeHandle());
}

AllocationStatus GrallocAllocator::importBuffer(
    const NativeHandle& handle,
    const BufferDescriptor& descriptor,
    std::unique_ptr<GraphicBuffer>& outBuffer
) {
    if (!handle.isValid()) {
        return AllocationStatus::ERROR_GRALLOC_FAILURE;
    }
    
    std::lock_guard<std::mutex> lock(allocMutex_);
    
    // Create buffer from imported handle
    NativeHandle importedHandle = handle;  // Would be registerBuffer
    
    outBuffer = std::make_unique<GraphicBuffer>(descriptor, importedHandle, this);
    activeBuffers_[outBuffer->getBufferId()] = outBuffer.get();
    
    return AllocationStatus::SUCCESS;
}

BufferUsage GrallocAllocator::getSupportedUsage() const {
    return BufferUsage::CPU_READ_OFTEN | BufferUsage::CPU_WRITE_OFTEN |
           BufferUsage::GPU_TEXTURE | BufferUsage::GPU_RENDER_TARGET |
           BufferUsage::CAMERA_INPUT | BufferUsage::CAMERA_OUTPUT |
           BufferUsage::VIDEO_ENCODER | BufferUsage::VIDEO_DECODER |
           BufferUsage::COMPOSER_OVERLAY;
}

bool GrallocAllocator::isFormatSupported(
    PixelFormat format,
    BufferUsage usage
) const {
    // Simplified - real implementation would query gralloc
    switch (format) {
        case PixelFormat::RGBA_8888:
        case PixelFormat::RGBX_8888:
        case PixelFormat::RGB_888:
        case PixelFormat::RGB_565:
        case PixelFormat::NV21:
        case PixelFormat::NV12:
        case PixelFormat::YV12:
        case PixelFormat::RAW10:
        case PixelFormat::RAW16:
        case PixelFormat::BLOB:
            return true;
        default:
            return false;
    }
}

bool GrallocAllocator::queryFormatInfo(
    PixelFormat format,
    BufferUsage usage,
    uint32_t& outStride
) const {
    // Would query gralloc for actual stride
    outStride = 0;  // Let gralloc decide
    return isFormatSupported(format, usage);
}

std::string GrallocAllocator::dumpState() const {
    std::ostringstream ss;
    ss << "GrallocAllocator State:\n";
    ss << "  Version: " << static_cast<int>(version_) << "\n";
    ss << "  Active buffers: " << activeBuffers_.size() << "\n";
    ss << "  Cache hit rate: " << (cache_->getHitRate() * 100) << "%\n";
    return ss.str();
}

bool GrallocAllocator::initializeHal() {
    // Platform-specific HAL initialization
    // gralloc = hardware::graphics::allocator::V4_0::IAllocator::getService();
    halHandle_ = nullptr;  // Would be HAL interface
    return true;
}

void GrallocAllocator::shutdownHal() {
    halHandle_ = nullptr;
}

AllocationStatus GrallocAllocator::allocateInternal(
    const BufferDescriptor& descriptor,
    NativeHandle& outHandle
) {
    // Real implementation would call:
    // gralloc->allocate(mapper::V4_0::IMapper::BufferDescriptorInfo{...}, ...)
    
    // Simulate allocation
    outHandle.fd = 42;  // Would be real FD from gralloc
    outHandle.numFds = 1;
    outHandle.numInts = 8;
    
    // Store dimensions in handle data
    outHandle.data[0] = descriptor.width;
    outHandle.data[1] = descriptor.height;
    outHandle.data[2] = static_cast<int>(descriptor.format);
    
    return AllocationStatus::SUCCESS;
}

// GrallocMapper implementation

GrallocMapper::GrallocMapper(GrallocVersion version)
    : version_(version)
{
    // Initialize mapper HAL
    // mapper_ = hardware::graphics::mapper::V4_0::IMapper::getService();
}

GrallocMapper::~GrallocMapper() {
    mapperHandle_ = nullptr;
}

bool GrallocMapper::lock(
    const NativeHandle& handle,
    BufferUsage usage,
    const MappedRegion* region,
    void** outData
) {
    if (!handle.isValid()) {
        return false;
    }
    
    // Real implementation would call mapper->lock()
    *outData = nullptr;  // Would be actual mapped pointer
    return true;
}

bool GrallocMapper::unlock(const NativeHandle& handle, int* outFence) {
    if (!handle.isValid()) {
        return false;
    }
    
    // Real implementation would call mapper->unlock()
    if (outFence) {
        *outFence = -1;  // No fence on CPU unlock
    }
    return true;
}

bool GrallocMapper::getMetadata(
    const NativeHandle& handle,
    uint32_t metadataType,
    void* outData,
    size_t& size
) {
    if (!handle.isValid()) {
        return false;
    }
    
    // Real implementation would query metadata from gralloc4
    return false;  // Not implemented for simulation
}

// AllocatorFactory implementation

std::unique_ptr<IBufferAllocator> AllocatorFactory::createDefault() {
    return std::make_unique<GrallocAllocator>();
}

std::unique_ptr<IBufferAllocator> AllocatorFactory::create(const std::string& name) {
    if (name == "gralloc" || name == "gralloc4") {
        return std::make_unique<GrallocAllocator>(GrallocVersion::GRALLOC_4_0);
    } else if (name == "gralloc3") {
        return std::make_unique<GrallocAllocator>(GrallocVersion::GRALLOC_3_0);
    } else if (name == "gralloc2") {
        return std::make_unique<GrallocAllocator>(GrallocVersion::GRALLOC_2_0);
    }
    
    // Default fallback
    return createDefault();
}

} // namespace graphics
} // namespace android
