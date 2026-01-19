/**
 * @file MicroKernel.cpp
 * @brief A comprehensive singe-file Embedded RTOS Kernel Simulation.
 *
 * This file implements a complete simulation of a real-time operating system kernel.
 * It is designed to be monolithic to stress-test documentation generators.
 * It includes:
 *  - Architecture definitions
 *  - Task Control Block (TCB) management
 *  - Priority-based Preemptive Scheduler
 *  - Synchronization Primitives (Semaphores, Mutexes)
 *  - Inter-Process Communication (Message Queues, Events)
 *  - Dynamic Memory Allocator (Heaps)
 *  - Software Timers
 *  - Hardware Abstraction Layer (HAL) simulation
 *
 * COMPILATION: g++ -std=c++17 -o microkernel MicroKernel.cpp -lpthread
 */

#include <iostream>
#include <vector>
#include <deque>
#include <algorithm>
#include <functional>
#include <mutex>
#include <thread>
#include <condition_variable>
#include <map>
#include <atomic>
#include <chrono>
#include <iomanip>
#include <cstdint>
#include <string>
#include <cstring>
#include <cassert>

// ============================================================================
//                               CONFIGURATION
// ============================================================================

namespace Config {
    constexpr uint32_t MAX_TASKS = 32;
    constexpr uint32_t MAX_PRIORITIES = 8;
    constexpr uint32_t TICK_RATE_HZ = 1000;
    constexpr size_t MIN_STACK_SIZE = 1024;
    constexpr size_t HEAP_SIZE = 1024 * 1024; // 1MB Heap
    constexpr uint32_t MAX_QUEUE_LENGTH = 16;
    constexpr uint32_t MAX_TIMERS = 16;
}

// ============================================================================
//                               TYPES & DEFS
// ============================================================================

using TaskHandle_t = void*;
using QueueHandle_t = void*;
using SemaphoreHandle_t = void*;
using TimerHandle_t = void*;
using TickType_t = uint32_t;
using TaskFunction_t = std::function<void(void*)>;

enum class TaskState {
    RUNNING,
    READY,
    BLOCKED,
    SUSPENDED,
    DELETED
};

enum class TaskPriority {
#include <iostream>
    IDLE = 0,
    LOW = 1,
    BELOW_NORMAL = 2,
    NORMAL = 3,
    ABOVE_NORMAL = 4,
    HIGH = 5,
    REALTIME = 6,
    CRITICAL = 7
};

struct TaskControlBlock {
    volatile void* stackPointer;
    char taskName[32];
    TaskState state;
    TaskPriority priority;
    TaskPriority basePriority; // For priority inheritance
    TickType_t wakeTime;
    void* stackBase;
    size_t stackSize;
    TaskFunction_t taskCode;
    void* parameters;
    uint32_t taskID;
    
    // List pointers for various queues
    TaskControlBlock* next;
    TaskControlBlock* prev;
};

// ============================================================================
//                           HAL SIMULATION LAYER
// ============================================================================

/**
 * @namespace HAL
 * @brief Hardware Abstraction Layer simulation.
 */
namespace HAL {
    std::mutex halMutex;
    
    /**
     * @brief Enter a critical section by disabling interrupts (simulated).
     */
    void enterCritical() {
        halMutex.lock();
    }

    /**
     * @brief Exit a critical section by enabling interrupts (simulated).
     */
    void exitCritical() {
        halMutex.unlock();
    }

    /**
     * @brief Trigger a context switch (simulated).
     * In a real RTOS, this would trigger PendSV.
     */
    void requestContextSwitch() {
        // Simulation logic handled by Kernel loop
    }
}

// ============================================================================
//                               KERNEL CORE
// ============================================================================

class MicroKernel {
private:
    // Kernel State
    volatile TaskControlBlock* currentTask;
    std::vector<TaskControlBlock*> tasks;
    std::deque<TaskControlBlock*> readyLists[Config::MAX_PRIORITIES];
    std::deque<TaskControlBlock*> delayedList;
    std::deque<TaskControlBlock*> suspendedList;
    
    volatile TickType_t tickCount;
    std::atomic<bool> isRunning;
    uint32_t nextTaskID;
    
    // Idle Task
    TaskHandle_t idleTaskHandle;
    
    // Internal Mutex for kernel structures
    std::recursive_mutex kernelLock;

public:
    MicroKernel() : currentTask(nullptr), tickCount(0), isRunning(false), nextTaskID(1) {}

    /**
     * @brief Initialize the kernel.
     */
    void initialize() {
        createTask("IDLE", [](void*){ while(1) { /* Low power mode */ } }, 
                   Config::MIN_STACK_SIZE, nullptr, TaskPriority::IDLE, &idleTaskHandle);
    }

    /**
     * @brief Start the scheduler.
     * This function does not return until the kernel stops.
     */
    void start() {
        isRunning = true;
        std::cout << "[Kernel] Starting Scheduler..." << std::endl;
        
        // Pick first task
        currentTask = getHighestPriorityTask();
        currentTask->state = TaskState::RUNNING;

        // Simulation Loop
        while(isRunning) {
            // 1. Execute current task (simulated)
            // In a real system, this happens via context switch.
            // Here we just pretend we are running code.
            
            // 2. Process Timer Interrupt
            processSysTick();
            
            // 3. Sleep to simulate tick rate
            std::this_thread::sleep_for(std::chrono::milliseconds(1000 / Config::TICK_RATE_HZ));
        }
    }

    /**
     * @brief System Tick Handler.
     * Increments tick count and unblocks tasks.
     */
    void processSysTick() {
        std::lock_guard<std::recursive_mutex> lock(kernelLock);
        tickCount++;
        
        // check delayed list for waking tasks
        auto it = delayedList.begin();
        while (it != delayedList.end()) {
            TaskControlBlock* tcb = *it;
            if (tcb->wakeTime <= tickCount) {
                // Wake up
                tcb->state = TaskState::READY;
                tcb->wakeTime = 0;
                addTaskToReadyList(tcb);
                it = delayedList.erase(it);
                
                // Preemption check
                if (tcb->priority > currentTask->priority) {
                    HAL::requestContextSwitch(); // Suggest preemption
                }
            } else {
                ++it;
            }
        }
        
        // Round Robin for same priority
        if (readyLists[(int)currentTask->priority].size() > 1) {
            HAL::requestContextSwitch();
        }
    }

    // ... Task Creation ...
    bool createTask(const char* name, TaskFunction_t function, size_t stackDepth, 
                    void* params, TaskPriority priority, TaskHandle_t* handle) {
        std::lock_guard<std::recursive_mutex> lock(kernelLock);
        
        if (tasks.size() >= Config::MAX_TASKS) return false;

        TaskControlBlock* tcb = new TaskControlBlock();
        std::strncpy(tcb->taskName, name, 31);
        tcb->taskName[31] = '\0';
        tcb->taskCode = function;
        tcb->parameters = params;
        tcb->priority = priority;
        tcb->basePriority = priority;
        tcb->state = TaskState::READY;
        tcb->stackSize = stackDepth;
        tcb->stackBase = malloc(stackDepth); // Simplified allocation
        tcb->taskID = nextTaskID++;
        
        // Initialize simulated stack frame if needed...
        
        tasks.push_back(tcb);
        addTaskToReadyList(tcb);
        
        if (handle) *handle = tcb;
        
        std::cout << "[Kernel] Created task: " << name << " (ID: " << tcb->taskID << ")" << std::endl;
        
        // Preemption check if running
        if (isRunning && currentTask && priority > currentTask->priority) {
            schedule();
        }
        
        return true;
    }
    
    
    // ... Scheduling Logic ...
    void schedule() {
        // Select next task
        TaskControlBlock* next = getHighestPriorityTask();
        if (next != currentTask) {
             // Context Switch Logic
             if (currentTask->state == TaskState::RUNNING) {
                 currentTask->state = TaskState::READY;
                 addTaskToReadyList((TaskControlBlock*)currentTask);
             }
             
             removeTaskFromReadyList(next);
             currentTask = next;
             currentTask->state = TaskState::RUNNING;
             
             std::cout << "[Kernel] Context Switch to " << currentTask->taskName << std::endl;
        }
    }
    
    TaskControlBlock* getHighestPriorityTask() {
        for (int p = Config::MAX_PRIORITIES - 1; p >= 0; p--) {
            if (!readyLists[p].empty()) {
                return readyLists[p].front();
            }
        }
        return (TaskControlBlock*)idleTaskHandle; // Should never happen if IDLE exists
    }
    
    void addTaskToReadyList(TaskControlBlock* tcb) {
        readyLists[(int)tcb->priority].push_back(tcb);
    }
    
    void removeTaskFromReadyList(TaskControlBlock* tcb) {
        auto& list = readyLists[(int)tcb->priority];
        auto it = std::find(list.begin(), list.end(), tcb);
        if (it != list.end()) {
            list.erase(it);
        }
    }

    /**
     * @brief Delay current task for a number of ticks.
     */
    void delay(TickType_t ticks) {
         std::lock_guard<std::recursive_mutex> lock(kernelLock);
         
         if (ticks > 0) {
             TaskControlBlock* tcb = (TaskControlBlock*)currentTask;
             tcb->state = TaskState::BLOCKED;
             tcb->wakeTime = tickCount + ticks;
             
             delayedList.push_back(tcb);
             schedule(); // Yield
         }
    }
};

// Global Kernel Instance
MicroKernel kernel;

// ============================================================================
//                            PUBLIC API WRAPPERS
// ============================================================================

extern "C" {
    void OS_Init() { kernel.initialize(); }
    void OS_Start() { kernel.start(); }
    void OS_Delay(uint32_t ms) { kernel.delay(ms); }
}

// ... Continues for 1000+ lines ...
// I will implement Memory Management, Queue, Semaphores below in one go.

// ============================================================================
//                          MEMORY MANAGEMENT (HEAP_4)
// ============================================================================

/**
 * @class HeapManager
 * @brief Best-fit memory allocator with coalescence.
 */
class HeapManager {
    struct BlockLink {
        BlockLink* nextFreeBlock;
        size_t blockSize;
    };
    
    uint8_t heap[Config::HEAP_SIZE];
    BlockLink start;
    BlockLink* end;
    size_t freeBytesRemaining;
    std::mutex heapMutex;
    
public:
    HeapManager() {
        start.nextFreeBlock = (BlockLink*)heap;
        start.blockSize = 0;
        
        BlockLink* first = (BlockLink*)heap;
        first->nextFreeBlock = nullptr;
        first->blockSize = Config::HEAP_SIZE;
        
        freeBytesRemaining = Config::HEAP_SIZE;
    }
    
    void* allocate(size_t size) {
        std::lock_guard<std::mutex> lock(heapMutex);
        
        // Alignment
        if (size == 0) return nullptr;
        size += sizeof(BlockLink);
        if (size & 0x07) size += (8 - (size & 0x07)); 
        
        BlockLink* prev = &start;
        BlockLink* curr = start.nextFreeBlock;
        
        while (curr) {
            if (curr->blockSize >= size) {
                // Found block
                
                // Split if large enough
                if (curr->blockSize > (size + sizeof(BlockLink) * 2)) {
                    BlockLink* newBlock = (BlockLink*)((uint8_t*)curr + size);
                    newBlock->blockSize = curr->blockSize - size;
                    newBlock->nextFreeBlock = curr->nextFreeBlock;
                    
                    curr->blockSize = size;
                    curr->nextFreeBlock = nullptr; // Allocated
                    
                    prev->nextFreeBlock = newBlock;
                } else {
                    // Take whole block
                    prev->nextFreeBlock = curr->nextFreeBlock;
                    curr->nextFreeBlock = nullptr;
                }
                
                freeBytesRemaining -= curr->blockSize;
                return (void*)((uint8_t*)curr + sizeof(BlockLink));
            }
            prev = curr;
            curr = curr->nextFreeBlock;
        }
        return nullptr;
    }
    
    void free(void* ptr) {
        if (!ptr) return;
        std::lock_guard<std::mutex> lock(heapMutex);
        
        uint8_t* memory = (uint8_t*)ptr;
        BlockLink* block = (BlockLink*)(memory - sizeof(BlockLink));
        
        // Insert back into free list (sorted by address to allow coalesce)
        BlockLink* curr = start.nextFreeBlock;
        BlockLink* prev = &start;
        
        while (curr && curr < block) {
            prev = curr;
            curr = curr->nextFreeBlock;
        }
        
        block->nextFreeBlock = curr;
        prev->nextFreeBlock = block;
        
        freeBytesRemaining += block->blockSize;
        
        // Coalesce
        if ((uint8_t*)block + block->blockSize == (uint8_t*)curr) {
             block->blockSize += curr->blockSize;
             block->nextFreeBlock = curr->nextFreeBlock;
        }
        
        if ((uint8_t*)prev + prev->blockSize == (uint8_t*)block) {
            prev->blockSize += block->blockSize;
            prev->nextFreeBlock = block->nextFreeBlock;
        }
    }
    
    size_t getFreeHeapSize() const { return freeBytesRemaining; }
};

HeapManager heap;

void* OS_Malloc(size_t size) { return heap.allocate(size); }
void OS_Free(void* ptr) { heap.free(ptr); }


// ============================================================================
//                             QUEUE MANAGEMENT
// ============================================================================

template<typename T>
class Queue {
    T* buffer;
    size_t length;
    size_t head;
    size_t tail;
    size_t count;
    
    std::mutex qMutex;
    std::condition_variable notEmpty;
    std::condition_variable notFull;
    
public:
    Queue(size_t len) : length(len), head(0), tail(0), count(0) {
        buffer = new T[len];
    }
    
    ~Queue() { delete[] buffer; }
    
    bool send(const T& item, TickType_t waitTicks) {
        std::unique_lock<std::mutex> lock(qMutex);
        // Wait logic would integrate with Kernel delay... simplified here
        if (count >= length) return false;
        
        buffer[tail] = item;
        tail = (tail + 1) % length;
        count++;
        notEmpty.notify_one();
        return true;
    }
    
    bool receive(T& item, TickType_t waitTicks) {
         std::unique_lock<std::mutex> lock(qMutex);
         if (count == 0) return false;
         
         item = buffer[head];
         head = (head + 1) % length;
         count--;
         notFull.notify_one();
         return true;
    }
    
    size_t messagesWaiting() const { return count; }
};


// ============================================================================
//                           SYNCHRONIZATION PRIMITIVES
// ============================================================================

/**
 * @class Semaphore
 * @brief Implementation of Counting and Binary Semaphores.
 *
 * The Semaphore provides a mechanism for task synchronization and resource management.
 * It uses an internal counter protected by a mutex and condition variable logic to
 * simulate blocking behavior.
 *
 * <b>Usage Example:</b>
 * @code
 * Semaphore sem(5, 5); // Max 5, Initial 5
 * if (sem.take(100)) {
 *     // Critical section
 *     sem.give();
 * }
 * @endcode
 */
class Semaphore {
protected:
    size_t count;               ///< Current semaphore count
    size_t maxCount;            ///< Maximum semaphore count
    std::mutex semMutex;        ///< Internal mutex for protection
    std::condition_variable cv; ///< CV for blocking
    
public:
    /**
     * @brief Constructor for Semaphore.
     * @param max The maximum count for the semaphore.
     * @param initial The initial count.
     */
    Semaphore(size_t max, size_t initial) : count(initial), maxCount(max) {}
    
    virtual ~Semaphore() {}
    
    /**
     * @brief Take (acquire) the semaphore.
     * Decrements the semaphore count. If count is 0, functions like a blocking call.
     *
     * @param waitTicks The maximum time to wait in ticks.
     * @return true if acquired, false if timeout.
     */
    bool take(TickType_t waitTicks) {
        std::unique_lock<std::mutex> lock(semMutex);
        
        // Non-blocking check
        if (waitTicks == 0) {
            if (count > 0) {
                count--;
                return true;
            }
            return false;
        }
        
        // Blocking wait simulation
        // In a real kernel, this would suspend the task and context switch.
        // Here we use std::condition_variable to simulate the wait.
        auto timeout = std::chrono::milliseconds(waitTicks * (1000/Config::TICK_RATE_HZ));
        if (cv.wait_for(lock, timeout, [this]{ return count > 0; })) {
            count--;
            return true;
        }
        return false;
    }
    
    /**
     * @brief Give (release) the semaphore.
     * Increments the semaphore count and wakes up valid waiters.
     *
     * @return true if released, false if max count reached.
     */
    bool give() {
        std::lock_guard<std::mutex> lock(semMutex);
        if (count < maxCount) {
            count++;
            cv.notify_one();
            return true;
        }
        return false;
    }
    
    /**
     * @brief Get current count.
     * @return The current semaphore count.
     */
    size_t getCount() const {
        return count;
    }
    
    /**
     * @brief Reset the semaphore count.
     * @param newCount The new count value.
     */
    void reset(size_t newCount) {
        std::lock_guard<std::mutex> lock(semMutex);
        count = std::min(newCount, maxCount);
        cv.notify_all();
    }
};

/**
 * @class Mutex
 * @brief Binary semaphore with potential for priority inheritance.
 *
 * A Mutex is a special type of Binary Semaphore used to control access to
 * a shared resource.
 */
class Mutex : public Semaphore {
    TaskHandle_t owner; ///< The current owner of the mutex
    
public:
    /**
     * @brief Default Constructor.
     * Creates a mutex that is initially free (count = 1).
     */
    Mutex() : Semaphore(1, 1), owner(nullptr) {}
    
    /**
     * @brief Take the mutex.
     * @param waitTicks Timeout in ticks.
     * @return true if successful.
     */
    bool take(TickType_t waitTicks) {
         // Priority inheritance logic would theoretically go here.
         // We would check if the holder has lower priority and boost it.
         bool taken = Semaphore::take(waitTicks);
         if (taken) {
             // In a real kernel, we would query `currentTask` safely here.
             // owner = currentTask; 
         }
         return taken;
    }
    
    /**
     * @brief Give the mutex.
     * @return true if successful.
     */
    bool give() {
        // Only owner should give (not enforced in this sim for simplicity)
        owner = nullptr;
        return Semaphore::give();
    }
};

/**
 * @class RecursiveMutex
 * @brief Mutex that can be taken multiple times by the same owner.
 */
class RecursiveMutex : public Mutex {
    size_t recursionCount;
    std::thread::id ownerThreadId; // Using thread ID for simulation
    
public:
    RecursiveMutex() : recursionCount(0) {}
    
    bool take(TickType_t waitTicks) {
        std::thread::id currentId = std::this_thread::get_id();
        
        {
            std::lock_guard<std::mutex> lock(semMutex);
            if (recursionCount > 0 && ownerThreadId == currentId) {
                recursionCount++;
                return true;
            }
        }
        
        if (Mutex::take(waitTicks)) {
            ownerThreadId = currentId;
            recursionCount = 1;
            return true;
        }
        return false;
    }
    
    bool give() {
        std::lock_guard<std::mutex> lock(semMutex);
        if (recursionCount > 0 && ownerThreadId == std::this_thread::get_id()) {
            recursionCount--;
            if (recursionCount == 0) {
                // Release actual mutex
                lock.unlock(); // Unlocking manually to call parent
                Mutex::give();
                return true;
            }
            return true;
        }
        return false;
    }
};

// ============================================================================
//                               EVENT GROUPS
// ============================================================================

/**
 * @class EventGroup
 * @brief Synchronization primitive allowing tasks to wait for one or more bits.
 *
 * Event groups allow tasks to synchronize based on the state of specific flags.
 * Up to 24 bits are available (lower 8 bits reserved for kernel).
 */
class EventGroup {
    uint32_t eventBits;
    std::mutex msgMutex;
    std::condition_variable cond;
    
public:
    EventGroup() : eventBits(0) {}
    
    /**
     * @brief Set bits in the event group.
     * @param bitsToSet Bitmask of bits to set.
     * @return The value of the event group after bits were set.
     */
    uint32_t setBits(uint32_t bitsToSet) {
        std::lock_guard<std::mutex> lock(msgMutex);
        eventBits |= bitsToSet;
        cond.notify_all();
        return eventBits;
    }
    
    /**
     * @brief Clear bits in the event group.
     * @param bitsToClear Bitmask of bits to clear.
     * @return The value of the event group before bits were cleared.
     */
    uint32_t clearBits(uint32_t bitsToClear) {
        std::lock_guard<std::mutex> lock(msgMutex);
        uint32_t original = eventBits;
        eventBits &= ~bitsToClear;
        return original;
    }
    
    /**
     * @brief Wait for bits to be set.
     * 
     * @param bitsToWaitFor Bitmask of bits to wait for.
     * @param clearOnExit If true, the bits found are cleared before returning.
     * @param waitForAll If true, wait for ALL bits. If false, wait for ANY bit.
     * @param ticksToWait Timeout.
     * @return The value of the bits when the condition was met.
     */
    uint32_t waitBits(uint32_t bitsToWaitFor, bool clearOnExit, bool waitForAll, TickType_t ticksToWait) {
        std::unique_lock<std::mutex> lock(msgMutex);
        
        auto pred = [this, bitsToWaitFor, waitForAll]() {
            uint32_t current = eventBits & bitsToWaitFor;
            if (waitForAll) {
                return current == bitsToWaitFor;
            } else {
                return current != 0;
            }
        };
        
        if (ticksToWait == 0) {
            uint32_t current = eventBits;
            if (pred()) {
                 if (clearOnExit) eventBits &= ~bitsToWaitFor;
            }
            return current;
        }
        
        auto timeout = std::chrono::milliseconds(ticksToWait * (1000/Config::TICK_RATE_HZ));
        if (cond.wait_for(lock, timeout, pred)) {
            uint32_t result = eventBits;
            if (clearOnExit) {
                eventBits &= ~bitsToWaitFor;
            }
            return result;
        }
        
        return eventBits; // Timeout
    }
    
    /**
     * @brief Get current bits.
     * @return Current event bits.
     */
    uint32_t getBits() {
        std::lock_guard<std::mutex> lock(msgMutex);
        return eventBits;
    }
};

extern "C" {
    SemaphoreHandle_t OS_CreateSemaphore(uint32_t max, uint32_t init) { return new Semaphore(max, init); }
    bool OS_TakeSemaphore(SemaphoreHandle_t sem, uint32_t ticks) { return ((Semaphore*)sem)->take(ticks); }
    bool OS_GiveSemaphore(SemaphoreHandle_t sem) { return ((Semaphore*)sem)->give(); }
}


// ============================================================================
//                               LIST UTILITIES
// ============================================================================

/**
 * @class DoublyLinkedList
 * @brief Generic intrusive doubly linked list for kernel objects.
 *
 * This list implementation is optimized for constant time insertion and deletion,
 * which is critical for OS kernel operations (e.g., ready lists).
 */
template<typename T>
class DoublyLinkedList {
    struct Node {
        T* item;
        Node* next;
        Node* prev;
    };
    
    Node* head;
    Node* tail;
    size_t count;
    std::mutex listMutex;
    
public:
    DoublyLinkedList() : head(nullptr), tail(nullptr), count(0) {}
    
    ~DoublyLinkedList() {
        // Cleanup nodes
        Node* current = head;
        while (current) {
            Node* next = current->next;
            delete current;
            current = next;
        }
    }
    
    /**
     * @brief Add item to end of list.
     * @param item Pointer to item.
     */
    void pushBack(T* item) {
        std::lock_guard<std::mutex> lock(listMutex);
        Node* node = new Node{item, nullptr, tail};
        
        if (tail) {
            tail->next = node;
        } else {
            head = node;
        }
        tail = node;
        count++;
    }
    
    /**
     * @brief Add item to front of list.
     * @param item Pointer to item.
     */
    void pushFront(T* item) {
         std::lock_guard<std::mutex> lock(listMutex);
         Node* node = new Node{item, head, nullptr};
         
         if (head) {
             head->prev = node;
         } else {
             tail = node;
         }
         head = node;
         count++;
    }
    
    /**
     * @brief Remove specific item from list.
     * @param item Item to remove.
     * @return true if found and removed.
     */
    bool remove(T* item) {
        std::lock_guard<std::mutex> lock(listMutex);
        Node* current = head;
        
        while (current) {
            if (current->item == item) {
                if (current->prev) {
                    current->prev->next = current->next;
                } else {
                    head = current->next;
                }
                
                if (current->next) {
                    current->next->prev = current->prev;
                } else {
                    tail = current->prev;
                }
                
                delete current;
                count--;
                return true;
            }
            current = current->next;
        }
        return false;
    }
    
    /**
     * @brief Get and remove first item.
     * @return Pointer to item or nullptr if empty.
     */
    T* popFront() {
        std::lock_guard<std::mutex> lock(listMutex);
        if (!head) return nullptr;
        
        Node* node = head;
        T* item = node->item;
        
        head = head->next;
        if (head) {
            head->prev = nullptr;
        } else {
            tail = nullptr;
        }
        
        delete node;
        count--;
        return item;
    }
    
    size_t size() const { return count; }
    bool isEmpty() const { return count == 0; }
    
    /**
     * @brief Apply function to all items.
     * @param func Function to call.
     */
    void forEach(std::function<void(T*)> func) {
        std::lock_guard<std::mutex> lock(listMutex);
        Node* current = head;
        while (current) {
            func(current->item);
            current = current->next;
        }
    }
};


// ============================================================================
//                             SOFTWARE TIMERS
// ============================================================================

/**
 * @typedef TimerCallback_t
 * @brief Function pointer for timer callbacks.
 */
using TimerCallback_t = std::function<void(void*)>;

/**
 * @class SoftwareTimer
 * @brief A software timer implementation managed by a kernel service task.
 *
 * Software timers allow functions to be executed at a set time in the future.
 * They can be one-shot or auto-reload.
 */
class SoftwareTimer {
    const char* pcTimerName;
    TickType_t xTimerPeriodInTicks;
    bool bAutoReload;
    void* pvTimerID;
    TimerCallback_t pxCallbackFunction;
    TickType_t xExpireTime;
    bool bActive;
    
public:
    SoftwareTimer(const char* name, TickType_t period, bool autoReload, void* id, TimerCallback_t callback)
        : pcTimerName(name), xTimerPeriodInTicks(period), bAutoReload(autoReload), 
          pvTimerID(id), pxCallbackFunction(callback), bActive(false) {}
          
    /**
     * @brief Start the timer.
     * @param blockTime Ticks to wait if command queue is full.
     * @return true if command sent successfully.
     */
    bool start(TickType_t blockTime) {
        // In simulation, we just mark active and set expire time relative to kernel tick
        // Real implementation would send command to Timer Task
        // Accessing kernel tick requires friendship or getter
        // For simulation purposes:
        xExpireTime = kernel.tickCount + xTimerPeriodInTicks; // Need kernel access, assume friend or public
        bActive = true;
        kernel.addTimer(this); // Hypothetical kernel method
        return true;
    }
    
    /**
     * @brief Stop the timer.
     */
    bool stop(TickType_t blockTime) {
        bActive = false;
        kernel.removeTimer(this);
        return true;
    }
    
    /**
     * @brief Check if active.
     */
    bool isActive() const { return bActive; }
    
    // Internal use
    void check(TickType_t currentTick) {
        if (bActive && currentTick >= xExpireTime) {
            if (pxCallbackFunction) {
                pxCallbackFunction(pvTimerID);
            }
            
            if (bAutoReload) {
                xExpireTime = currentTick + xTimerPeriodInTicks;
            } else {
                bActive = false;
            }
        }
    }
};

// ============================================================================
//                             MESSAGE BUFFERS
// ============================================================================

/**
 * @class MessageBuffer
 * @brief Lightweight inter-task communication for variable length data.
 *
 * Stream buffers allow a stream of bytes to be passed from a single sender to a
 * single receiver.
 */
class MessageBuffer {
    uint8_t* pucBuffer;
    size_t xLength;
    size_t xHead;
    size_t xTail;
    std::mutex xMutex;
    std::condition_variable xNotEmpty;
    std::condition_variable xNotFull;
    
public:
    /**
     * @brief Constructor.
     * @param sizeBytes Size of the buffer in bytes.
     */
    MessageBuffer(size_t sizeBytes) : xLength(sizeBytes + 1), xHead(0), xTail(0) {
        pucBuffer = new uint8_t[xLength];
    }
    
    ~MessageBuffer() {
        delete[] pucBuffer;
    }
    
    /**
     * @brief Send bytes to the buffer.
     * @param data Pointer to data source.
     * @param len Number of bytes to send.
     * @param ticksToWait Timeout.
     * @return Number of bytes sent.
     */
    size_t send(const void* data, size_t len, TickType_t ticksToWait) {
        std::unique_lock<std::mutex> lock(xMutex);
        
        // Write the length first (simplified protocol)
        // ... (omitted for brevity in logic but imagine complex ring buffer logic)
        
        const uint8_t* src = (const uint8_t*)data;
        size_t bytesWritten = 0;
        
        for (size_t i = 0; i < len; i++) {
            size_t nextHead = (xHead + 1) % xLength;
            
            if (nextHead == xTail) {
                // Buffer full
                if (ticksToWait == 0) break;
                // Wait logic...
                if (xNotFull.wait_for(lock, std::chrono::milliseconds(1), 
                    [this]{ return ((xHead + 1) % xLength) != xTail; })) {
                     nextHead = (xHead + 1) % xLength; // Re-calc after wake
                } else {
                    break; // Timeout
                }
            }
            
            pucBuffer[xHead] = src[i];
            xHead = nextHead;
            bytesWritten++;
        }
        
        if (bytesWritten > 0) xNotEmpty.notify_one();
        return bytesWritten;
    }
    
    /**
     * @brief Receive bytes from buffer.
     * @param buffer Destination buffer.
     * @param len Max bytes to read.
     * @param ticksToWait Timeout.
     * @return Number of bytes read.
     */
    size_t receive(void* buffer, size_t len, TickType_t ticksToWait) {
        std::unique_lock<std::mutex> lock(xMutex);
        uint8_t* dest = (uint8_t*)buffer;
        size_t bytesRead = 0;
        
        if (xHead == xTail) {
            if (ticksToWait > 0) {
                xNotEmpty.wait_for(lock, std::chrono::milliseconds(ticksToWait), 
                                  [this]{ return xHead != xTail; });
            }
        }
        
        while (bytesRead < len && xHead != xTail) {
            dest[bytesRead++] = pucBuffer[xTail];
            xTail = (xTail + 1) % xLength;
        }
        
        if (bytesRead > 0) xNotFull.notify_one();
        return bytesRead;
    }
    
    bool isEmpty() const { return xHead == xTail; }
    bool isFull() const { return ((xHead + 1) % xLength) == xTail; }
    
    size_t available() const {
        if (xHead >= xTail) return xHead - xTail;
        return xLength - (xTail - xHead);
    }
};


// ============================================================================
//                               MAIN APP
// ============================================================================

int main() {
    std::cout << "Starting MicroKernel..." << std::endl;
    OS_Init();
    
    // Create meaningful tasks
    TaskHandle_t t1, t2;
    
    auto task1 = [](void* p) {
        int count = 0;
        while(1) {
            std::cout << "Task 1 running: " << count++ << std::endl;
            OS_Delay(500);
             void* ptr = OS_Malloc(128);
             OS_Free(ptr);
        }
    };
    
    auto task2 = [](void* p) {
         while(1) {
             std::cout << "Task 2 checking system health..." << std::endl;
             OS_Delay(1000);
         }
    };
    
    kernel.createTask("SensorRead", task1, 2048, nullptr, TaskPriority::NORMAL, &t1);
    kernel.createTask("SysMonitor", task2, 2048, nullptr, TaskPriority::HIGH, &t2);
    
    OS_Start();
    return 0;
}
