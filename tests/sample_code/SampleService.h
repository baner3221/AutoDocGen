/**
 * Sample Android native service for AutoDocGen testing.
 * 
 * This demonstrates a typical Android framework service pattern
 * with Binder IPC, lifecycle management, and HAL interactions.
 */

#ifndef SAMPLE_SERVICE_H
#define SAMPLE_SERVICE_H

#include <string>
#include <vector>
#include <memory>
#include <mutex>

namespace android {
namespace sample {

/**
 * Configuration options for the SampleService.
 */
struct ServiceConfig {
    std::string serviceName;
    int maxConnections;
    bool enableLogging;
    int timeoutMs;
};

/**
 * Callback interface for service events.
 */
class IServiceCallback {
public:
    virtual ~IServiceCallback() = default;
    
    /**
     * Called when a client connects to the service.
     * 
     * @param clientId Unique identifier for the client
     * @param clientPid Process ID of the connecting client
     */
    virtual void onClientConnected(int clientId, int clientPid) = 0;
    
    /**
     * Called when a client disconnects.
     * 
     * @param clientId The client that disconnected
     */
    virtual void onClientDisconnected(int clientId) = 0;
    
    /**
     * Called when the service encounters an error.
     * 
     * @param errorCode Error code (see ServiceErrors enum)
     * @param errorMessage Human-readable error message
     */
    virtual void onError(int errorCode, const std::string& errorMessage) = 0;
};

/**
 * SampleService - A demonstration Android native service.
 * 
 * This service manages client connections and provides
 * data processing capabilities via Binder IPC.
 * 
 * Thread Safety:
 * - All public methods are thread-safe
 * - Internal state protected by mLock mutex
 * 
 * Lifecycle:
 * - Created by system_server during boot
 * - Runs for the lifetime of the system
 * - Clients connect/disconnect dynamically
 */
class SampleService {
public:
    /**
     * Construct a new SampleService.
     * 
     * @param config Configuration for the service
     * @param callback Optional callback for service events
     */
    explicit SampleService(
        const ServiceConfig& config,
        std::shared_ptr<IServiceCallback> callback = nullptr
    );
    
    ~SampleService();
    
    // Prevent copying
    SampleService(const SampleService&) = delete;
    SampleService& operator=(const SampleService&) = delete;
    
    /**
     * Initialize the service and register with ServiceManager.
     * 
     * This method performs the following:
     * 1. Validates the configuration
     * 2. Initializes internal state
     * 3. Registers with the Android ServiceManager
     * 4. Starts the worker thread pool
     * 
     * @return true if initialization succeeded, false otherwise
     * 
     * @note Must be called before any other methods
     * @note Thread-safe
     */
    bool initialize();
    
    /**
     * Process data from a client.
     * 
     * @param clientId The client making the request
     * @param inputData Raw input data to process
     * @param outputData Buffer to receive processed data
     * 
     * @return Number of bytes written to outputData, or -1 on error
     * 
     * @throws std::invalid_argument if clientId is not connected
     * @throws std::runtime_error if service is not initialized
     */
    int processData(
        int clientId,
        const std::vector<uint8_t>& inputData,
        std::vector<uint8_t>& outputData
    );
    
    /**
     * Get the number of currently connected clients.
     * 
     * @return Number of active client connections
     */
    size_t getClientCount() const;
    
    /**
     * Check if a specific client is connected.
     * 
     * @param clientId Client ID to check
     * @return true if client is connected
     */
    bool isClientConnected(int clientId) const;
    
    /**
     * Shutdown the service gracefully.
     * 
     * This will:
     * 1. Stop accepting new connections
     * 2. Wait for pending operations to complete
     * 3. Disconnect all clients
     * 4. Release resources
     * 
     * @param timeoutMs Maximum time to wait for shutdown (0 = indefinite)
     * @return true if shutdown completed within timeout
     */
    bool shutdown(int timeoutMs = 5000);

private:
    ServiceConfig mConfig;
    std::shared_ptr<IServiceCallback> mCallback;
    mutable std::mutex mLock;
    bool mInitialized;
    std::vector<int> mConnectedClients;
    
    // Internal helper methods
    bool validateConfig() const;
    void notifyClientEvent(int clientId, bool connected);
};

} // namespace sample
} // namespace android

#endif // SAMPLE_SERVICE_H
