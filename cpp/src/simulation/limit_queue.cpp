/**
 * @file limit_queue.cpp
 * @brief 涨跌停订单排队机制实现
 */

#include "simulation/limit_queue.h"
#include <algorithm>
#include <cmath>

namespace apexquant {
namespace simulation {

LimitQueue::LimitQueue() {
}

void LimitQueue::add_to_limit_up_queue(const SimulatedOrder& order) {
    std::lock_guard<std::mutex> lock(mutex_);
    limit_up_queues_[order.symbol].push_back(order);
}

void LimitQueue::add_to_limit_down_queue(const SimulatedOrder& order) {
    std::lock_guard<std::mutex> lock(mutex_);
    limit_down_queues_[order.symbol].push_back(order);
}

std::vector<SimulatedOrder> LimitQueue::try_fill_limit_up_orders(
    const std::string& symbol,
    const Tick& tick
) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<SimulatedOrder> filled_orders;
    
    auto it = limit_up_queues_.find(symbol);
    if (it == limit_up_queues_.end() || it->second.empty()) {
        return filled_orders;
    }
    
    // 检查是否仍在涨停
    bool still_at_limit = is_at_limit_up(symbol, tick.last_price, tick.last_close);
    
    if (!still_at_limit) {
        // 价格打开，所有排队订单可以成交
        filled_orders = std::move(it->second);
        limit_up_queues_.erase(it);
    } else {
        // 仍在涨停，模拟部分成交（10%的订单可能成交）
        auto& queue = it->second;
        size_t can_fill = std::max(size_t(1), queue.size() / 10);
        
        for (size_t i = 0; i < can_fill && i < queue.size(); ++i) {
            filled_orders.push_back(queue[i]);
        }
        
        // 移除已成交的订单
        queue.erase(queue.begin(), queue.begin() + can_fill);
    }
    
    return filled_orders;
}

std::vector<SimulatedOrder> LimitQueue::try_fill_limit_down_orders(
    const std::string& symbol,
    const Tick& tick
) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<SimulatedOrder> filled_orders;
    
    auto it = limit_down_queues_.find(symbol);
    if (it == limit_down_queues_.end() || it->second.empty()) {
        return filled_orders;
    }
    
    // 检查是否仍在跌停
    bool still_at_limit = is_at_limit_down(symbol, tick.last_price, tick.last_close);
    
    if (!still_at_limit) {
        // 价格打开，所有排队订单可以成交
        filled_orders = std::move(it->second);
        limit_down_queues_.erase(it);
    } else {
        // 仍在跌停，模拟部分成交（10%的订单可能成交）
        auto& queue = it->second;
        size_t can_fill = std::max(size_t(1), queue.size() / 10);
        
        for (size_t i = 0; i < can_fill && i < queue.size(); ++i) {
            filled_orders.push_back(queue[i]);
        }
        
        // 移除已成交的订单
        queue.erase(queue.begin(), queue.begin() + can_fill);
    }
    
    return filled_orders;
}

LimitStatus LimitQueue::check_limit_status(
    const std::string& symbol,
    double current_price,
    double last_close
) {
    if (last_close <= 0) {
        return LimitStatus::NORMAL;
    }
    
    if (is_at_limit_up(symbol, current_price, last_close)) {
        return LimitStatus::LIMIT_UP;
    }
    
    if (is_at_limit_down(symbol, current_price, last_close)) {
        return LimitStatus::LIMIT_DOWN;
    }
    
    return LimitStatus::NORMAL;
}

bool LimitQueue::remove_from_queue(const std::string& order_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // 在涨停队列中查找
    for (auto& [symbol, queue] : limit_up_queues_) {
        auto it = std::find_if(queue.begin(), queue.end(),
            [&order_id](const SimulatedOrder& order) {
                return order.order_id == order_id;
            });
        
        if (it != queue.end()) {
            queue.erase(it);
            return true;
        }
    }
    
    // 在跌停队列中查找
    for (auto& [symbol, queue] : limit_down_queues_) {
        auto it = std::find_if(queue.begin(), queue.end(),
            [&order_id](const SimulatedOrder& order) {
                return order.order_id == order_id;
            });
        
        if (it != queue.end()) {
            queue.erase(it);
            return true;
        }
    }
    
    return false;
}

size_t LimitQueue::get_limit_up_queue_size(const std::string& symbol) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = limit_up_queues_.find(symbol);
    return (it != limit_up_queues_.end()) ? it->second.size() : 0;
}

size_t LimitQueue::get_limit_down_queue_size(const std::string& symbol) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = limit_down_queues_.find(symbol);
    return (it != limit_down_queues_.end()) ? it->second.size() : 0;
}

void LimitQueue::clear_all_queues() {
    std::lock_guard<std::mutex> lock(mutex_);
    limit_up_queues_.clear();
    limit_down_queues_.clear();
}

double LimitQueue::get_limit_pct(const std::string& symbol) const {
    // 根据股票代码判断涨跌停幅度
    
    // ST股票：5%
    if (symbol.find("ST") != std::string::npos || 
        symbol.find("st") != std::string::npos) {
        return 0.05;
    }
    
    // 科创板（688开头）：20%
    if (symbol.length() >= 3 && symbol.substr(0, 3) == "688") {
        return 0.20;
    }
    
    // 创业板（300开头）：20%
    if (symbol.length() >= 3 && symbol.substr(0, 3) == "300") {
        return 0.20;
    }
    
    // 北交所（8或4开头）：30%
    if (symbol.length() >= 1 && (symbol[0] == '8' || symbol[0] == '4')) {
        return 0.30;
    }
    
    // 普通A股：10%
    return 0.10;
}

double LimitQueue::calculate_limit_up_price(const std::string& symbol, double last_close) const {
    double limit_pct = get_limit_pct(symbol);
    double limit_up = last_close * (1.0 + limit_pct);
    return std::round(limit_up * 100.0) / 100.0;
}

double LimitQueue::calculate_limit_down_price(const std::string& symbol, double last_close) const {
    double limit_pct = get_limit_pct(symbol);
    double limit_down = last_close * (1.0 - limit_pct);
    return std::round(limit_down * 100.0) / 100.0;
}

bool LimitQueue::is_at_limit_up(const std::string& symbol, double price, double last_close) const {
    if (last_close <= 0) return false;
    
    double limit_up = calculate_limit_up_price(symbol, last_close);
    
    // 价格在涨停价附近（0.01元误差）
    return std::abs(price - limit_up) < 0.01;
}

bool LimitQueue::is_at_limit_down(const std::string& symbol, double price, double last_close) const {
    if (last_close <= 0) return false;
    
    double limit_down = calculate_limit_down_price(symbol, last_close);
    
    // 价格在跌停价附近（0.01元误差）
    return std::abs(price - limit_down) < 0.01;
}

} // namespace simulation
} // namespace apexquant





