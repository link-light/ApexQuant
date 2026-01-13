#pragma once

#include <string>
#include <thread>
#include <atomic>
#include <chrono>
#include <functional>
#include <memory>

namespace apexquant {
namespace trading {

/**
 * @brief 连接管理器 - 心跳检测和断线重连
 */
class ConnectionManager {
public:
    ConnectionManager();
    ~ConnectionManager();
    
    /**
     * @brief 启动心跳检测
     * @param heartbeat_interval 心跳间隔（秒）
     * @param timeout 超时时间（秒）
     */
    void start_heartbeat(int heartbeat_interval = 30, int timeout = 60);
    
    /**
     * @brief 停止心跳检测
     */
    void stop_heartbeat();
    
    /**
     * @brief 更新最后活动时间
     */
    void update_last_activity();
    
    /**
     * @brief 设置心跳回调
     */
    void set_heartbeat_callback(std::function<bool()> callback);
    
    /**
     * @brief 设置断线回调
     */
    void set_disconnect_callback(std::function<void()> callback);
    
    /**
     * @brief 设置重连回调
     */
    void set_reconnect_callback(std::function<bool()> callback);
    
    /**
     * @brief 启用自动重连
     */
    void enable_auto_reconnect(bool enable = true, int max_retries = 5);
    
    /**
     * @brief 检查是否运行中
     */
    bool is_running() const { return running_; }
    
    /**
     * @brief 获取重连次数
     */
    int get_reconnect_count() const { return reconnect_count_; }
    
private:
    void heartbeat_loop();
    bool try_reconnect();
    
    std::atomic<bool> running_;
    std::unique_ptr<std::thread> heartbeat_thread_;
    
    int heartbeat_interval_;
    int timeout_;
    std::chrono::steady_clock::time_point last_activity_;
    
    bool auto_reconnect_;
    int max_retries_;
    std::atomic<int> reconnect_count_;
    
    std::function<bool()> heartbeat_callback_;
    std::function<void()> disconnect_callback_;
    std::function<bool()> reconnect_callback_;
};

} // namespace trading
} // namespace apexquant

