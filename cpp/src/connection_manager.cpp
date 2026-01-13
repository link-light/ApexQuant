#include "connection_manager.h"
#include <iostream>

namespace apexquant {
namespace trading {

ConnectionManager::ConnectionManager()
    : running_(false),
      heartbeat_interval_(30),
      timeout_(60),
      auto_reconnect_(false),
      max_retries_(5),
      reconnect_count_(0) {
    update_last_activity();
}

ConnectionManager::~ConnectionManager() {
    stop_heartbeat();
}

void ConnectionManager::start_heartbeat(int heartbeat_interval, int timeout) {
    if (running_) {
        return;
    }
    
    heartbeat_interval_ = heartbeat_interval;
    timeout_ = timeout;
    running_ = true;
    reconnect_count_ = 0;
    
    update_last_activity();
    
    heartbeat_thread_ = std::make_unique<std::thread>(&ConnectionManager::heartbeat_loop, this);
}

void ConnectionManager::stop_heartbeat() {
    if (!running_) {
        return;
    }
    
    running_ = false;
    
    if (heartbeat_thread_ && heartbeat_thread_->joinable()) {
        heartbeat_thread_->join();
    }
}

void ConnectionManager::update_last_activity() {
    last_activity_ = std::chrono::steady_clock::now();
}

void ConnectionManager::set_heartbeat_callback(std::function<bool()> callback) {
    heartbeat_callback_ = callback;
}

void ConnectionManager::set_disconnect_callback(std::function<void()> callback) {
    disconnect_callback_ = callback;
}

void ConnectionManager::set_reconnect_callback(std::function<bool()> callback) {
    reconnect_callback_ = callback;
}

void ConnectionManager::enable_auto_reconnect(bool enable, int max_retries) {
    auto_reconnect_ = enable;
    max_retries_ = max_retries;
}

void ConnectionManager::heartbeat_loop() {
    while (running_) {
        std::this_thread::sleep_for(std::chrono::seconds(heartbeat_interval_));
        
        if (!running_) break;
        
        // 检查超时
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - last_activity_).count();
        
        if (elapsed > timeout_) {
            std::cout << "连接超时，尝试重连..." << std::endl;
            
            // 触发断线回调
            if (disconnect_callback_) {
                disconnect_callback_();
            }
            
            // 尝试重连
            if (auto_reconnect_) {
                bool reconnected = try_reconnect();
                if (reconnected) {
                    std::cout << "重连成功" << std::endl;
                    update_last_activity();
                } else {
                    std::cout << "重连失败，停止服务" << std::endl;
                    running_ = false;
                    break;
                }
            } else {
                running_ = false;
                break;
            }
        } else {
            // 发送心跳
            if (heartbeat_callback_) {
                bool success = heartbeat_callback_();
                if (success) {
                    update_last_activity();
                }
            }
        }
    }
}

bool ConnectionManager::try_reconnect() {
    if (!reconnect_callback_) {
        return false;
    }
    
    for (int i = 0; i < max_retries_; ++i) {
        reconnect_count_++;
        
        std::cout << "第 " << (i + 1) << " 次重连尝试..." << std::endl;
        
        bool success = reconnect_callback_();
        if (success) {
            return true;
        }
        
        // 指数退避
        int wait_time = (1 << i);  // 2^i 秒
        std::this_thread::sleep_for(std::chrono::seconds(wait_time));
    }
    
    return false;
}

} // namespace trading
} // namespace apexquant

