/**
 * @file BufferPool.cpp
 * @brief Implementation of BufferPool class
 */

#include "BufferPool.h"
#include <algorithm>
#include <chrono>

namespace android {
namespace graphics {

BufferPool::BufferPool(
    std::shared_ptr<IBufferAllocator> allocator,
    const BufferDescriptor& descriptor,
    const BufferPoolConfig& config
)
    : allocator_(std::move(allocator))
    , descriptor_(descriptor)
    , config_(config)
{
    // Pre-allocate initial buffers
    grow(config_.preAllocate);
}

BufferPool::~BufferPool() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Clear all buffers
    while (!freeBuffers_.empty()) {
        freeBuffers_.pop();
    }
    allBuffers_.clear();
}

GraphicBuffer* BufferPool::acquireBuffer() {
    return acquireBuffer(config_.blockTimeoutMs);
}

GraphicBuffer* BufferPool::acquireBuffer(uint32_t timeoutMs) {
    std::unique_lock<std::mutex> lock(mutex_);
    
    auto deadline = std::chrono::steady_clock::now() + 
                    std::chrono::milliseconds(timeoutMs);
    
    while (freeBuffers_.empty()) {
        // Try to grow the pool
        if (allBuffers_.size() < config_.maxBuffers) {
            lock.unlock();
            if (grow(config_.growthCount) > 0) {
                lock.lock();
                continue;
            }
            lock.lock();
        }
        
        // Wait if blocking is allowed
        if (!config_.allowBlocking || timeoutMs == 0) {
            // Notify listeners
            for (auto* listener : listeners_) {
                listener->onPoolExhausted(this);
            }
            return nullptr;
        }
        
        if (bufferAvailable_.wait_until(lock, deadline) == 
            std::cv_status::timeout) {
            return nullptr;
        }
    }
    
    GraphicBuffer* buffer = freeBuffers_.front();
    freeBuffers_.pop();
    
    stats_.allocationCount++;
    notifyBufferAcquired(buffer);
    
    return buffer;
}

void BufferPool::releaseBuffer(GraphicBuffer* buffer) {
    if (!buffer) return;
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Verify buffer belongs to this pool
    auto it = std::find_if(allBuffers_.begin(), allBuffers_.end(),
        [buffer](const std::unique_ptr<GraphicBuffer>& b) {
            return b.get() == buffer;
        });
    
    if (it == allBuffers_.end()) {
        return;  // Not our buffer
    }
    
    freeBuffers_.push(buffer);
    stats_.reuseCount++;
    
    notifyBufferReleased(buffer);
    bufferAvailable_.notify_one();
}

uint32_t BufferPool::grow(uint32_t count) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    uint32_t added = 0;
    for (uint32_t i = 0; i < count; ++i) {
        if (allBuffers_.size() >= config_.maxBuffers) {
            break;
        }
        
        std::unique_ptr<GraphicBuffer> buffer;
        AllocationStatus status = allocator_->allocate(descriptor_, buffer);
        
        if (status == AllocationStatus::SUCCESS && buffer) {
            freeBuffers_.push(buffer.get());
            allBuffers_.push_back(std::move(buffer));
            added++;
            
            stats_.totalBuffers++;
            stats_.freeBuffers++;
            stats_.allocatedBytes += descriptor_.calculateSize();
            
            if (stats_.allocatedBytes > stats_.peakAllocatedBytes) {
                stats_.peakAllocatedBytes = stats_.allocatedBytes;
            }
        }
    }
    
    if (added > 0) {
        notifyPoolGrew(static_cast<uint32_t>(allBuffers_.size()));
        bufferAvailable_.notify_all();
    }
    
    return added;
}

uint32_t BufferPool::shrink(uint32_t keepCount) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    uint32_t freed = 0;
    
    while (freeBuffers_.size() > keepCount && 
           allBuffers_.size() > config_.minBuffers) {
        GraphicBuffer* buffer = freeBuffers_.front();
        freeBuffers_.pop();
        
        // Find and remove from allBuffers
        auto it = std::find_if(allBuffers_.begin(), allBuffers_.end(),
            [buffer](const std::unique_ptr<GraphicBuffer>& b) {
                return b.get() == buffer;
            });
        
        if (it != allBuffers_.end()) {
            stats_.allocatedBytes -= descriptor_.calculateSize();
            stats_.totalBuffers--;
            stats_.freeBuffers--;
            allBuffers_.erase(it);
            freed++;
        }
    }
    
    if (freed > 0) {
        notifyPoolShrunk(static_cast<uint32_t>(allBuffers_.size()));
    }
    
    return freed;
}

bool BufferPool::flush(uint32_t timeoutMs) {
    auto deadline = std::chrono::steady_clock::now() + 
                    std::chrono::milliseconds(timeoutMs);
    
    std::unique_lock<std::mutex> lock(mutex_);
    
    while (freeBuffers_.size() < allBuffers_.size()) {
        if (std::chrono::steady_clock::now() >= deadline) {
            return false;
        }
        
        bufferAvailable_.wait_until(lock, deadline);
    }
    
    return true;
}

PoolStatistics BufferPool::getStatistics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    PoolStatistics stats = stats_;
    stats.freeBuffers = freeBuffers_.size();
    
    if (stats.allocationCount > 0) {
        stats.hitRate = static_cast<double>(stats.reuseCount) / 
                        stats.allocationCount;
    }
    
    return stats;
}

void BufferPool::addListener(BufferPoolListener* listener) {
    std::lock_guard<std::mutex> lock(mutex_);
    listeners_.push_back(listener);
}

void BufferPool::removeListener(BufferPoolListener* listener) {
    std::lock_guard<std::mutex> lock(mutex_);
    listeners_.erase(
        std::remove(listeners_.begin(), listeners_.end(), listener),
        listeners_.end()
    );
}

uint32_t BufferPool::getFreeCount() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return static_cast<uint32_t>(freeBuffers_.size());
}

uint32_t BufferPool::getTotalCount() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return static_cast<uint32_t>(allBuffers_.size());
}

bool BufferPool::isFull() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return allBuffers_.size() >= config_.maxBuffers;
}

bool BufferPool::isEmpty() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return freeBuffers_.empty();
}

void BufferPool::notifyBufferAcquired(GraphicBuffer* buffer) {
    for (auto* listener : listeners_) {
        listener->onBufferAcquired(this, buffer);
    }
}

void BufferPool::notifyBufferReleased(GraphicBuffer* buffer) {
    for (auto* listener : listeners_) {
        listener->onBufferReleased(this, buffer);
    }
}

void BufferPool::notifyPoolGrew(uint32_t newTotal) {
    for (auto* listener : listeners_) {
        listener->onPoolGrew(this, newTotal);
    }
}

void BufferPool::notifyPoolShrunk(uint32_t newTotal) {
    for (auto* listener : listeners_) {
        listener->onPoolShrunk(this, newTotal);
    }
}

} // namespace graphics
} // namespace android
