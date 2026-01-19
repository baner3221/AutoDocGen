# Codebase Overview

<div class="mermaid">
classDiagram
    class TaskControlBlock {
        <<struct>>
    }
    class MicroKernel {
        +MicroKernel()
        +initialize()
        +start()
        +processSysTick()
        +createTask(...)
        +schedule()
        +getHighestPriorityTask()
        +addTaskToReadyList(tcb)
        +removeTaskFromReadyList(tcb)
        +delay(ticks)
    }
    class HeapManager {
        +HeapManager()
        +allocate(size)
        +free(ptr)
        +getFreeHeapSize()
    }
    class Semaphore {
        +Semaphore(max, initial)
        +destroy_Semaphore()
        +take(waitTicks)
        +give()
        +getCount()
        +reset(newCount)
    }
    class Mutex {
        +Mutex()
        +take(waitTicks)
        +give()
    }
    class RecursiveMutex {
        +RecursiveMutex()
        +take(waitTicks)
        +give()
    }
    class EventGroup {
        +EventGroup()
        +setBits(bitsToSet)
        +clearBits(bitsToClear)
        +waitBits(...)
        +getBits()
    }
    class SoftwareTimer {
        +SoftwareTimer(...)
        +start(blockTime)
        +stop(blockTime)
        +isActive()
        +check(currentTick)
    }
    class MessageBuffer {
        +MessageBuffer(sizeBytes)
        +destroy_MessageBuffer()
        +send(...)
        +receive(...)
        +isEmpty()
        +isFull()
        +available()
    }
    MicroKernel o-- TaskControlBlock : currentTask
    Semaphore <|-- Mutex
    Mutex <|-- RecursiveMutex
</div>
