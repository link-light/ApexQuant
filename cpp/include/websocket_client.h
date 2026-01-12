#pragma once

#include <string>
#include <functional>
#include <memory>
#include <thread>
#include <atomic>
#include "data_structures.h"

namespace apexquant {

/**
 * @brief WebSocket 客户端回调函数类型
 */
using MessageCallback = std::function<void(const std::string&)>;
using TickCallback = std::function<void(const Tick&)>;
using ErrorCallback = std::function<void(const std::string&)>;

/**
 * @brief 简单的 WebSocket 客户端（Day 2 简化版）
 * 
 * 注意：完整实现需要 Boost.Beast 或 websocketpp
 * 这里提供接口定义，实际网络功能将在后续完善
 */
class WebSocketClient {
public:
    WebSocketClient(const std::string& url);
    ~WebSocketClient();
    
    // 连接和断开
    bool connect();
    void disconnect();
    bool is_connected() const;
    
    // 订阅行情
    void subscribe(const std::string& symbol);
    void unsubscribe(const std::string& symbol);
    
    // 设置回调
    void set_message_callback(MessageCallback callback);
    void set_tick_callback(TickCallback callback);
    void set_error_callback(ErrorCallback callback);
    
    // 发送消息
    void send(const std::string& message);
    
private:
    void run();
    void process_message(const std::string& message);
    
    std::string url_;
    std::atomic<bool> connected_;
    std::atomic<bool> running_;
    
    std::unique_ptr<std::thread> thread_;
    
    MessageCallback message_callback_;
    TickCallback tick_callback_;
    ErrorCallback error_callback_;
};

} // namespace apexquant

