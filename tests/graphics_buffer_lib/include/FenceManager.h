/**
 * @file FenceManager.h
 * @brief Synchronization fence management for buffer operations
 * 
 * Provides abstraction over sync fences for GPU/CPU synchronization
 * in graphics buffer workflows.
 */

#pragma once

#include <cstdint>
#include <memory>
#include <vector>
#include <functional>
#include <atomic>
#include <mutex>

namespace android {
namespace graphics {

// Forward declarations
class GraphicBuffer;
class BufferPool;

/**
 * @brief Fence state enumeration
 */
enum class FenceState {
    UNSIGNALED,
    SIGNALED,
    ERROR,
    INVALID
};

/**
 * @brief Represents a synchronization fence
 */
class Fence {
public:
    /**
     * @brief Create an invalid fence
     */
    Fence();
    
    /**
     * @brief Create a fence from file descriptor
     * @param fd Fence file descriptor (takes ownership)
     */
    explicit Fence(int fd);
    
    /**
     * @brief Move constructor
     */
    Fence(Fence&& other) noexcept;
    
    /**
     * @brief Destructor - closes fence FD
     */
    ~Fence();
    
    // Non-copyable
    Fence(const Fence&) = delete;
    Fence& operator=(const Fence&) = delete;
    
    /**
     * @brief Move assignment
     */
    Fence& operator=(Fence&& other) noexcept;
    
    /**
     * @brief Wait for fence to signal
     * @param timeoutMs Maximum wait time (UINT32_MAX = infinite)
     * @return True if signaled, false on timeout or error
     */
    bool wait(uint32_t timeoutMs = UINT32_MAX);
    
    /**
     * @brief Check if fence is signaled without waiting
     */
    bool isSignaled() const;
    
    /**
     * @brief Get current fence state
     */
    FenceState getState() const;
    
    /**
     * @brief Get fence file descriptor (does not transfer ownership)
     */
    int getFd() const { return fd_; }
    
    /**
     * @brief Duplicate the fence FD
     * @return New FD (caller owns) or -1 on failure
     */
    int dup() const;
    
    /**
     * @brief Check if fence is valid
     */
    bool isValid() const { return fd_ >= 0; }
    
    explicit operator bool() const { return isValid(); }
    
    /**
     * @brief Create a signaled fence (no-op fence)
     */
    static Fence createSignaled();
    
    /**
     * @brief Merge multiple fences into one
     * @param fences Fences to merge
     * @return Merged fence (signals when all inputs signal)
     */
    static Fence merge(const std::vector<Fence>& fences);
    
    /**
     * @brief Merge two fences
     */
    static Fence merge(Fence&& a, Fence&& b);
    
    /**
     * @brief Get fence signal time (if signaled)
     * @return Signal time in nanoseconds, or -1
     */
    int64_t getSignalTime() const;

private:
    int fd_ = -1;
};

/**
 * @brief Manager for fence lifecycle and operations
 * 
 * Provides:
 * - Fence creation and tracking
 * - Async wait with callbacks
 * - Fence statistics
 * - Debug timeline info
 */
class FenceManager {
public:
    /**
     * @brief Callback when fence signals
     */
    using SignalCallback = std::function<void(Fence* fence, FenceState state)>;
    
    FenceManager();
    ~FenceManager();
    
    /**
     * @brief Create a new timeline fence
     * @param name Debug name for the fence
     * @return Created fence
     */
    Fence createFence(const char* name = nullptr);
    
    /**
     * @brief Signal a fence (for CPU-signaled fences)
     * @param fence Fence to signal
     * @return True on success
     */
    bool signalFence(Fence& fence);
    
    /**
     * @brief Wait for fence asynchronously
     * @param fence Fence to wait on
     * @param callback Called when fence signals
     */
    void waitAsync(Fence&& fence, SignalCallback callback);
    
    /**
     * @brief Wait for multiple fences
     * @param fences Fences to wait on
     * @param waitAll If true, wait for all; else wait for any
     * @param timeoutMs Maximum wait time
     * @return Index of signaled fence (or -1 on timeout)
     */
    int waitMultiple(
        const std::vector<Fence*>& fences,
        bool waitAll,
        uint32_t timeoutMs = UINT32_MAX
    );
    
    /**
     * @brief Get number of active fences
     */
    size_t getActiveFenceCount() const;
    
    /**
     * @brief Dump fence timeline for debugging
     */
    std::string dumpTimeline() const;
    
    /**
     * @brief Associate a fence with a buffer
     */
    void associateFenceWithBuffer(Fence* fence, GraphicBuffer* buffer);

private:
    struct FenceInfo {
        std::unique_ptr<Fence> fence;
        std::string name;
        int64_t createTime;
        GraphicBuffer* associatedBuffer = nullptr;
    };
    
    std::vector<FenceInfo> activeFences_;
    mutable std::mutex mutex_;
    
    std::atomic<uint64_t> fenceCounter_{0};
    
    void cleanupSignaled();
};

} // namespace graphics
} // namespace android
