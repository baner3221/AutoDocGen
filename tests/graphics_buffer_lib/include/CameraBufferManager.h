/**
 * @file CameraBufferManager.h
 * @brief Camera-specific buffer management layer
 * 
 * Interfaces with the Android camera framework to provide optimized
 * buffer allocation and streaming for camera capture pipelines.
 */

#pragma once

#include "BufferPool.h"
#include "IBufferAllocator.h"
#include "BufferTypes.h"
#include <map>
#include <vector>
#include <memory>
#include <functional>

namespace android {
namespace graphics {

// Forward declarations
class StreamConfiguration;
class CaptureRequest;
class CaptureResult;
class FenceManager;

/**
 * @brief Stream types for camera buffer management
 */
enum class StreamType {
    OUTPUT_PREVIEW,
    OUTPUT_VIDEO,
    OUTPUT_STILL,
    OUTPUT_RAW,
    INPUT_REPROCESS
};

/**
 * @brief Stream state enumeration
 */
enum class StreamState {
    IDLE,
    CONFIGURED,
    STREAMING,
    ERROR
};

/**
 * @brief Configuration for a single camera stream
 */
struct StreamConfiguration {
    uint32_t streamId = 0;
    StreamType type = StreamType::OUTPUT_PREVIEW;
    BufferDescriptor bufferDesc;
    BufferPoolConfig poolConfig;
    uint32_t rotation = 0;
    bool useCase = false;  ///< Hint for gralloc optimization
    
    std::string toString() const;
};

/**
 * @brief Camera buffer manager for multi-stream scenarios
 * 
 * Manages buffer pools for multiple camera streams, providing:
 * - Per-stream buffer allocation
 * - Stream reconfiguration
 * - Buffer queueing/dequeuing
 * - Fence synchronization
 * 
 * Thread Safety:
 * - All public methods are thread-safe
 * - Callbacks may be invoked from worker threads
 * 
 * @see BufferPool for underlying pool management
 */
class CameraBufferManager : public BufferPoolListener {
public:
    /**
     * @brief Callback for buffer availability
     */
    using BufferCallback = std::function<void(uint32_t streamId, GraphicBuffer* buffer)>;
    
    /**
     * @brief Callback for errors
     */
    using ErrorCallback = std::function<void(uint32_t streamId, AllocationStatus error)>;
    
    /**
     * @brief Create a camera buffer manager
     * @param allocator Allocator to use for all streams
     */
    explicit CameraBufferManager(std::shared_ptr<IBufferAllocator> allocator);
    
    /**
     * @brief Create with custom fence manager
     */
    CameraBufferManager(
        std::shared_ptr<IBufferAllocator> allocator,
        std::shared_ptr<FenceManager> fenceManager
    );
    
    ~CameraBufferManager() override;
    
    /**
     * @brief Configure a new stream
     * @param config Stream configuration
     * @return Stream ID (0 on failure)
     */
    uint32_t configureStream(const StreamConfiguration& config);
    
    /**
     * @brief Reconfigure an existing stream
     * @param streamId Stream to reconfigure
     * @param newConfig New configuration
     * @return True on success
     */
    bool reconfigureStream(
        uint32_t streamId,
        const StreamConfiguration& newConfig
    );
    
    /**
     * @brief Remove a stream
     * @param streamId Stream to remove
     * @param waitForBuffers If true, wait for all buffers to be returned
     * @return True on success
     */
    bool removeStream(uint32_t streamId, bool waitForBuffers = true);
    
    /**
     * @brief Dequeue a buffer for a stream (producer side)
     * @param streamId Target stream
     * @param[out] outFenceFd Acquire fence (-1 if none)
     * @return Buffer or nullptr if not available
     */
    GraphicBuffer* dequeueBuffer(uint32_t streamId, int* outFenceFd = nullptr);
    
    /**
     * @brief Queue a filled buffer (producer side)
     * @param streamId Target stream
     * @param buffer Buffer to queue
     * @param releaseFenceFd Release fence (-1 if none)
     * @return True on success
     */
    bool queueBuffer(
        uint32_t streamId,
        GraphicBuffer* buffer,
        int releaseFenceFd = -1
    );
    
    /**
     * @brief Acquire a buffer for consumption (consumer side)
     * @param streamId Source stream
     * @param[out] outFenceFd Acquire fence
     * @return Buffer or nullptr
     */
    GraphicBuffer* acquireBuffer(uint32_t streamId, int* outFenceFd = nullptr);
    
    /**
     * @brief Release a consumed buffer (consumer side)
     * @param streamId Source stream
     * @param buffer Buffer to release
     * @param releaseFenceFd Release fence
     */
    void releaseBuffer(
        uint32_t streamId,
        GraphicBuffer* buffer,
        int releaseFenceFd = -1
    );
    
    /**
     * @brief Set callback for buffer availability
     */
    void setBufferCallback(BufferCallback callback);
    
    /**
     * @brief Set callback for errors
     */
    void setErrorCallback(ErrorCallback callback);
    
    /**
     * @brief Get stream state
     */
    StreamState getStreamState(uint32_t streamId) const;
    
    /**
     * @brief Get all configured stream IDs
     */
    std::vector<uint32_t> getConfiguredStreams() const;
    
    /**
     * @brief Get statistics for a stream
     */
    PoolStatistics getStreamStatistics(uint32_t streamId) const;
    
    /**
     * @brief Flush all streams
     * @param timeoutMs Maximum wait time
     * @return True if all streams flushed
     */
    bool flushAllStreams(uint32_t timeoutMs = 5000);
    
    /**
     * @brief Dump state for debugging
     */
    std::string dumpState() const;
    
    // BufferPoolListener implementation
    void onBufferAcquired(BufferPool* pool, GraphicBuffer* buffer) override;
    void onBufferReleased(BufferPool* pool, GraphicBuffer* buffer) override;
    void onPoolExhausted(BufferPool* pool) override;

private:
    struct StreamInfo {
        StreamConfiguration config;
        std::unique_ptr<BufferPool> pool;
        StreamState state = StreamState::IDLE;
        std::queue<GraphicBuffer*> pendingBuffers;
        std::mutex mutex;
    };
    
    std::shared_ptr<IBufferAllocator> allocator_;
    std::shared_ptr<FenceManager> fenceManager_;
    
    std::map<uint32_t, std::unique_ptr<StreamInfo>> streams_;
    mutable std::mutex streamsMutex_;
    
    BufferCallback bufferCallback_;
    ErrorCallback errorCallback_;
    
    std::atomic<uint32_t> nextStreamId_{1};
    
    StreamInfo* getStream(uint32_t streamId);
    const StreamInfo* getStream(uint32_t streamId) const;
};

} // namespace graphics
} // namespace android
