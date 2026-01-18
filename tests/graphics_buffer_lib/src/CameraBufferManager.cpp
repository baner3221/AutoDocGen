/**
 * @file CameraBufferManager.cpp
 * @brief Implementation of CameraBufferManager class
 */

#include "CameraBufferManager.h"
#include "FenceManager.h"
#include <sstream>
#include <algorithm>

namespace android {
namespace graphics {

std::string StreamConfiguration::toString() const {
    std::ostringstream ss;
    ss << "Stream[id=" << streamId 
       << " type=" << static_cast<int>(type)
       << " " << bufferDesc.toString()
       << " rotation=" << rotation << "]";
    return ss.str();
}

CameraBufferManager::CameraBufferManager(
    std::shared_ptr<IBufferAllocator> allocator
)
    : allocator_(std::move(allocator))
    , fenceManager_(std::make_shared<FenceManager>())
{
}

CameraBufferManager::CameraBufferManager(
    std::shared_ptr<IBufferAllocator> allocator,
    std::shared_ptr<FenceManager> fenceManager
)
    : allocator_(std::move(allocator))
    , fenceManager_(std::move(fenceManager))
{
}

CameraBufferManager::~CameraBufferManager() {
    flushAllStreams(1000);
    
    std::lock_guard<std::mutex> lock(streamsMutex_);
    streams_.clear();
}

uint32_t CameraBufferManager::configureStream(const StreamConfiguration& config) {
    std::lock_guard<std::mutex> lock(streamsMutex_);
    
    uint32_t streamId = nextStreamId_.fetch_add(1);
    
    auto info = std::make_unique<StreamInfo>();
    info->config = config;
    info->config.streamId = streamId;
    
    // Create buffer pool for this stream
    info->pool = std::make_unique<BufferPool>(
        allocator_,
        config.bufferDesc,
        config.poolConfig
    );
    
    // Register as listener
    info->pool->addListener(this);
    
    info->state = StreamState::CONFIGURED;
    
    streams_[streamId] = std::move(info);
    
    return streamId;
}

bool CameraBufferManager::reconfigureStream(
    uint32_t streamId,
    const StreamConfiguration& newConfig
) {
    std::lock_guard<std::mutex> lock(streamsMutex_);
    
    auto it = streams_.find(streamId);
    if (it == streams_.end()) {
        return false;
    }
    
    StreamInfo* info = it->second.get();
    
    // Can only reconfigure if idle or configured
    if (info->state == StreamState::STREAMING) {
        return false;
    }
    
    // Remove old pool
    info->pool->removeListener(this);
    
    // Create new pool with new config
    info->config = newConfig;
    info->config.streamId = streamId;
    
    info->pool = std::make_unique<BufferPool>(
        allocator_,
        newConfig.bufferDesc,
        newConfig.poolConfig
    );
    info->pool->addListener(this);
    
    return true;
}

bool CameraBufferManager::removeStream(uint32_t streamId, bool waitForBuffers) {
    std::lock_guard<std::mutex> lock(streamsMutex_);
    
    auto it = streams_.find(streamId);
    if (it == streams_.end()) {
        return false;
    }
    
    StreamInfo* info = it->second.get();
    
    if (waitForBuffers) {
        info->pool->flush(5000);
    }
    
    info->pool->removeListener(this);
    streams_.erase(it);
    
    return true;
}

GraphicBuffer* CameraBufferManager::dequeueBuffer(
    uint32_t streamId,
    int* outFenceFd
) {
    StreamInfo* info = getStream(streamId);
    if (!info) return nullptr;
    
    GraphicBuffer* buffer = info->pool->acquireBuffer();
    
    if (buffer && outFenceFd) {
        // Create acquire fence
        Fence fence = fenceManager_->createFence("camera_dequeue");
        *outFenceFd = fence.dup();
    }
    
    return buffer;
}

bool CameraBufferManager::queueBuffer(
    uint32_t streamId,
    GraphicBuffer* buffer,
    int releaseFenceFd
) {
    StreamInfo* info = getStream(streamId);
    if (!info || !buffer) return false;
    
    // Handle release fence
    if (releaseFenceFd >= 0) {
        buffer->setAcquireFence(fenceManager_.get(), releaseFenceFd);
    }
    
    // Add to pending queue for consumers
    {
        std::lock_guard<std::mutex> lock(info->mutex);
        info->pendingBuffers.push(buffer);
    }
    
    // Notify callback
    if (bufferCallback_) {
        bufferCallback_(streamId, buffer);
    }
    
    return true;
}

GraphicBuffer* CameraBufferManager::acquireBuffer(
    uint32_t streamId,
    int* outFenceFd
) {
    StreamInfo* info = getStream(streamId);
    if (!info) return nullptr;
    
    std::lock_guard<std::mutex> lock(info->mutex);
    
    if (info->pendingBuffers.empty()) {
        return nullptr;
    }
    
    GraphicBuffer* buffer = info->pendingBuffers.front();
    info->pendingBuffers.pop();
    
    if (outFenceFd) {
        *outFenceFd = -1;  // Consumer's acquire fence
    }
    
    return buffer;
}

void CameraBufferManager::releaseBuffer(
    uint32_t streamId,
    GraphicBuffer* buffer,
    int releaseFenceFd
) {
    StreamInfo* info = getStream(streamId);
    if (!info || !buffer) return;
    
    // Wait for consumer's release fence
    if (releaseFenceFd >= 0) {
        Fence fence(releaseFenceFd);
        fence.wait(1000);
    }
    
    // Return buffer to pool
    info->pool->releaseBuffer(buffer);
}

void CameraBufferManager::setBufferCallback(BufferCallback callback) {
    bufferCallback_ = std::move(callback);
}

void CameraBufferManager::setErrorCallback(ErrorCallback callback) {
    errorCallback_ = std::move(callback);
}

StreamState CameraBufferManager::getStreamState(uint32_t streamId) const {
    const StreamInfo* info = getStream(streamId);
    return info ? info->state : StreamState::ERROR;
}

std::vector<uint32_t> CameraBufferManager::getConfiguredStreams() const {
    std::lock_guard<std::mutex> lock(streamsMutex_);
    
    std::vector<uint32_t> ids;
    ids.reserve(streams_.size());
    
    for (const auto& [id, info] : streams_) {
        ids.push_back(id);
    }
    
    return ids;
}

PoolStatistics CameraBufferManager::getStreamStatistics(uint32_t streamId) const {
    const StreamInfo* info = getStream(streamId);
    if (!info) return {};
    
    return info->pool->getStatistics();
}

bool CameraBufferManager::flushAllStreams(uint32_t timeoutMs) {
    std::lock_guard<std::mutex> lock(streamsMutex_);
    
    bool success = true;
    for (auto& [id, info] : streams_) {
        if (!info->pool->flush(timeoutMs)) {
            success = false;
        }
    }
    
    return success;
}

std::string CameraBufferManager::dumpState() const {
    std::ostringstream ss;
    ss << "CameraBufferManager State:\n";
    
    std::lock_guard<std::mutex> lock(streamsMutex_);
    
    ss << "  Configured streams: " << streams_.size() << "\n";
    
    for (const auto& [id, info] : streams_) {
        ss << "  " << info->config.toString() << "\n";
        ss << "    State: " << static_cast<int>(info->state) << "\n";
        
        auto stats = info->pool->getStatistics();
        ss << "    Pool: " << stats.freeBuffers << "/" << stats.totalBuffers 
           << " free, hit rate=" << (stats.hitRate * 100) << "%\n";
    }
    
    return ss.str();
}

void CameraBufferManager::onBufferAcquired(
    BufferPool* pool,
    GraphicBuffer* buffer
) {
    // Could update stream state to STREAMING
}

void CameraBufferManager::onBufferReleased(
    BufferPool* pool,
    GraphicBuffer* buffer
) {
    // Could update statistics
}

void CameraBufferManager::onPoolExhausted(BufferPool* pool) {
    // Find stream ID and notify error
    std::lock_guard<std::mutex> lock(streamsMutex_);
    
    for (const auto& [id, info] : streams_) {
        if (info->pool.get() == pool) {
            if (errorCallback_) {
                errorCallback_(id, AllocationStatus::ERROR_NO_MEMORY);
            }
            break;
        }
    }
}

CameraBufferManager::StreamInfo* CameraBufferManager::getStream(uint32_t streamId) {
    std::lock_guard<std::mutex> lock(streamsMutex_);
    
    auto it = streams_.find(streamId);
    return it != streams_.end() ? it->second.get() : nullptr;
}

const CameraBufferManager::StreamInfo* CameraBufferManager::getStream(
    uint32_t streamId
) const {
    std::lock_guard<std::mutex> lock(streamsMutex_);
    
    auto it = streams_.find(streamId);
    return it != streams_.end() ? it->second.get() : nullptr;
}

} // namespace graphics
} // namespace android
