# Codebase Overview

<div class="mermaid">
classDiagram
    class android_graphics_BufferCacheEntry {
        <<struct>>
    }
    class android_graphics_BufferCache {
        +BufferCache(maxEntries)
        +destroy_BufferCache()
        +lookup(bufferId)
        +insert(entry)
        +invalidate(bufferId)
        +clear()
        +size()
        +getHitRate()
        +resize(newMaxEntries)
    }
    class android_graphics_BufferLockGuard {
        +BufferLockGuard(buffer, mode)
        +BufferLockGuard(...)
        +destroy_BufferLockGuard()
        +BufferLockGuard(arg0)
        +op__assign(arg0)
        +BufferLockGuard(other)
        +op_ bool()
        +getRawData()
        +getSize()
        +unlock()
    }
    class android_graphics_BufferMapper {
        +copyFromBuffer(buffer, dest, size)
        +copyToBuffer(buffer, src, size)
        +fillBuffer(buffer, value)
        +processBuffer(buffer, processor)
        +calculateStride(format, width)
        +getBytesPerPixel(format)
        +isYuvFormat(format)
        +isCompressedFormat(format)
    }
    class android_graphics_BufferPoolConfig {
        <<struct>>
    }
    class android_graphics_BufferPool {
        +BufferPool(...)
        +destroy_BufferPool()
        +BufferPool(arg0)
        +op__assign(arg0)
        +acquireBuffer()
        +acquireBuffer(timeoutMs)
        +releaseBuffer(buffer)
        +grow(count)
        +shrink(keepCount)
        +flush(timeoutMs)
    }
    class android_graphics_BufferPoolListener {
        +destroy_BufferPoolListener()
        +onBufferAcquired(pool, buffer)
        +onBufferReleased(pool, buffer)
        +onPoolGrew(pool, newTotal)
        +onPoolShrunk(pool, newTotal)
        +onPoolExhausted(pool)
    }
    class android_graphics_BufferDescriptor {
        <<struct>>
        +calculateSize()
        +isValid()
        +toString()
    }
    class android_graphics_NativeHandle {
        <<struct>>
        +isValid()
        +close()
    }
    class android_graphics_MappedRegion {
        <<struct>>
        +isLocked()
    }
    class android_graphics_PoolStatistics {
        <<struct>>
    }
    class android_graphics_StreamConfiguration {
        <<struct>>
        +toString()
    }
    class android_graphics_CameraBufferManager {
        +CameraBufferManager(allocator)
        +CameraBufferManager(...)
        +destroy_CameraBufferManager()
        +configureStream(config)
        +reconfigureStream(streamId, newConfig)
        +removeStream(...)
        +dequeueBuffer(streamId, outFenceFd)
        +queueBuffer(...)
        +acquireBuffer(streamId, outFenceFd)
        +releaseBuffer(...)
    }
    class android_graphics_Fence {
        +Fence()
        +Fence(fd)
        +Fence(other)
        +destroy_Fence()
        +Fence(arg0)
        +op__assign(arg0)
        +op__assign(other)
        +wait(timeoutMs)
        +isSignaled()
        +getState()
    }
    class android_graphics_FenceManager {
        +FenceManager()
        +destroy_FenceManager()
        +createFence(name)
        +signalFence(fence)
        +waitAsync(fence, callback)
        +waitMultiple(...)
        +getActiveFenceCount()
        +dumpTimeline()
        +associateFenceWithBuffer(fence, buffer)
    }
    class android_graphics_GrallocAllocator {
        +GrallocAllocator()
        +GrallocAllocator(version)
        +destroy_GrallocAllocator()
        +allocate(...)
        +allocateAsync(descriptor, callback)
        +free(buffer)
        +importBuffer(...)
        +getSupportedUsage()
        +isFormatSupported(format, usage)
        +getName()
    }
    class android_graphics_GrallocMapper {
        +GrallocMapper(version)
        +destroy_GrallocMapper()
        +lock(...)
        +unlock(handle, outFence)
        +getMetadata(...)
    }
    class android_graphics_GraphicBuffer {
        +GraphicBuffer(...)
        +GraphicBuffer(other)
        +destroy_GraphicBuffer()
        +GraphicBuffer(arg0)
        +op__assign(arg0)
        +lockForRead(outRegion)
        +lockForWrite(outRegion)
        +lockRegion(...)
        +unlock()
        +duplicateHandle()
    }
    class android_graphics_Version {
        <<struct>>
    }
    class android_graphics_IBufferAllocator {
        +destroy_IBufferAllocator()
        +allocate(...)
        +allocateAsync(descriptor, callback)
        +free(buffer)
        +importBuffer(...)
        +getSupportedUsage()
        +isFormatSupported(format, usage)
        +getName()
    }
    class android_graphics_AllocatorFactory {
        +createDefault()
        +create(name)
    }
    android_graphics_BufferCacheEntry *-- android_graphics_BufferDescriptor : descriptor
    android_graphics_BufferCacheEntry *-- android_graphics_NativeHandle : handle
    android_graphics_BufferLockGuard o-- android_graphics_GraphicBuffer : buffer_
    android_graphics_BufferLockGuard *-- android_graphics_MappedRegion : region_
    android_graphics_BufferPool *-- android_graphics_BufferDescriptor : descriptor_
    android_graphics_BufferPool *-- android_graphics_BufferPoolConfig : config_
    android_graphics_BufferPool *-- android_graphics_PoolStatistics : stats_
    android_graphics_StreamConfiguration *-- android_graphics_BufferDescriptor : bufferDesc
    android_graphics_StreamConfiguration *-- android_graphics_BufferPoolConfig : poolConfig
    android_graphics_BufferPoolListener <|-- android_graphics_CameraBufferManager
    android_graphics_IBufferAllocator <|-- android_graphics_GrallocAllocator
    android_graphics_GraphicBuffer *-- android_graphics_BufferDescriptor : descriptor_
    android_graphics_GraphicBuffer *-- android_graphics_NativeHandle : handle_
    android_graphics_GraphicBuffer o-- android_graphics_IBufferAllocator : allocator_
    android_graphics_GraphicBuffer *-- android_graphics_MappedRegion : mappedRegion_
    android_graphics_GraphicBuffer o-- android_graphics_FenceManager : fenceManager_
</div>
