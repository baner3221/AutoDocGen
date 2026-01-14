/**
 * Implementation of SampleService.
 */

#include "SampleService.h"
#include <algorithm>
#include <stdexcept>

namespace android {
namespace sample {

SampleService::SampleService(
    const ServiceConfig& config,
    std::shared_ptr<IServiceCallback> callback
) : mConfig(config),
    mCallback(std::move(callback)),
    mInitialized(false) {
}

SampleService::~SampleService() {
    if (mInitialized) {
        shutdown(0);
    }
}

bool SampleService::initialize() {
    std::lock_guard<std::mutex> lock(mLock);
    
    if (mInitialized) {
        return true; // Already initialized
    }
    
    if (!validateConfig()) {
        return false;
    }
    
    // Register with ServiceManager (simulated)
    // In real Android, this would call: sp<IServiceManager> sm = defaultServiceManager();
    
    mInitialized = true;
    return true;
}

int SampleService::processData(
    int clientId,
    const std::vector<uint8_t>& inputData,
    std::vector<uint8_t>& outputData
) {
    std::lock_guard<std::mutex> lock(mLock);
    
    if (!mInitialized) {
        throw std::runtime_error("Service not initialized");
    }
    
    if (!isClientConnected(clientId)) {
        throw std::invalid_argument("Client not connected");
    }
    
    // Simulate data processing
    outputData = inputData;
    for (auto& byte : outputData) {
        byte ^= 0xFF; // Simple XOR transform
    }
    
    return static_cast<int>(outputData.size());
}

size_t SampleService::getClientCount() const {
    std::lock_guard<std::mutex> lock(mLock);
    return mConnectedClients.size();
}

bool SampleService::isClientConnected(int clientId) const {
    // Note: caller should hold mLock if thread safety needed
    return std::find(mConnectedClients.begin(), mConnectedClients.end(), clientId) 
           != mConnectedClients.end();
}

bool SampleService::shutdown(int timeoutMs) {
    std::lock_guard<std::mutex> lock(mLock);
    
    if (!mInitialized) {
        return true;
    }
    
    // Notify all clients
    for (int clientId : mConnectedClients) {
        notifyClientEvent(clientId, false);
    }
    
    mConnectedClients.clear();
    mInitialized = false;
    
    return true;
}

bool SampleService::validateConfig() const {
    if (mConfig.serviceName.empty()) {
        return false;
    }
    if (mConfig.maxConnections <= 0) {
        return false;
    }
    if (mConfig.timeoutMs < 0) {
        return false;
    }
    return true;
}

void SampleService::notifyClientEvent(int clientId, bool connected) {
    if (mCallback) {
        if (connected) {
            mCallback->onClientConnected(clientId, 0);
        } else {
            mCallback->onClientDisconnected(clientId);
        }
    }
}

} // namespace sample
} // namespace android
