/**
 * @file simulated_exchange.cpp
 * @brief ApexQuant模拟交易所实现
 */

#include "simulation/simulated_exchange.h"
#include <chrono>
#include <sstream>
#include <iomanip>
#include <cmath>

namespace apexquant {
namespace simulation {

SimulatedExchange::SimulatedExchange(
    const std::string& account_id, 
    double initial_capital
) : account_(account_id, initial_capital),
    matcher_(),
    current_time_(0),
    order_counter_(0) {
}

// ============================================================================
// 订单管理
// ============================================================================

std::string SimulatedExchange::submit_order(SimulatedOrder order) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // 1. 生成唯一订单ID
    order.order_id = generate_order_id(order.symbol);
    order.status = OrderStatus::PENDING;
    order.filled_volume = 0;
    order.submit_time = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
    
    // 2. 验证订单参数
    if (order.volume <= 0) {
        order.status = OrderStatus::REJECTED;
        orders_[order.order_id] = order;
        return order.order_id;
    }
    
    if (order.type == OrderType::LIMIT && order.price <= 0) {
        order.status = OrderStatus::REJECTED;
        orders_[order.order_id] = order;
        return order.order_id;
    }
    
    // 3. 冻结资金或持仓
    if (order.side == OrderSide::BUY) {
        // 买单：冻结资金（预估金额 * 1.003 包含手续费）
        double estimate_price = order.type == OrderType::LIMIT ? order.price : 1000000.0;  // 市价单用极大值
        double freeze_amount = order.volume * estimate_price * 1.003;
        
        if (!account_.freeze_cash(freeze_amount)) {
            order.status = OrderStatus::REJECTED;
            orders_[order.order_id] = order;
            return order.order_id;
        }
        
    } else {
        // 卖单：冻结持仓（需要检查T+1）
        int64_t current_date = current_time_ / (24 * 3600 * 1000);  // 简化：从毫秒转天数
        
        if (!account_.can_sell(order.symbol, order.volume, current_date)) {
            order.status = OrderStatus::REJECTED;
            orders_[order.order_id] = order;
            return order.order_id;
        }
        
        if (!account_.freeze_position(order.symbol, order.volume)) {
            order.status = OrderStatus::REJECTED;
            orders_[order.order_id] = order;
            return order.order_id;
        }
    }
    
    // 4. 保存订单
    orders_[order.order_id] = order;
    
    return order.order_id;
}

void SimulatedExchange::on_tick(const Tick& tick) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    current_time_ = tick.timestamp;
    int64_t current_date = current_time_ / (24 * 3600 * 1000);
    
    // 1. 更新该symbol所有持仓的市值
    account_.update_position_price(tick.symbol, tick.last_price);
    
    // 2. 遍历该symbol的PENDING订单，尝试撮合
    for (auto& pair : orders_) {
        SimulatedOrder& order = pair.second;
        
        if (order.status != OrderStatus::PENDING) {
            continue;
        }
        
        if (order.symbol != tick.symbol) {
            continue;
        }
        
        // 3. 调用撮合引擎
        MatchResult result = matcher_.try_match_order(order, tick, true);
        
        if (result.success) {
            // 成交
            process_fill(order, result, current_date);
        } else {
            // 拒绝（例如价格不满足、涨跌停等）
            // 注意：限价单不满足条件不算拒绝，保持PENDING
            if (result.reject_reason.find("limit") == std::string::npos &&
                result.reject_reason.find("price") == std::string::npos) {
                process_reject(order, result.reject_reason);
            }
        }
    }
}

bool SimulatedExchange::cancel_order(const std::string& order_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = orders_.find(order_id);
    if (it == orders_.end()) {
        return false;
    }
    
    SimulatedOrder& order = it->second;
    
    if (order.status != OrderStatus::PENDING) {
        return false;  // 只能撤销PENDING订单
    }
    
    // 解冻资金或持仓
    if (order.side == OrderSide::BUY) {
        double estimate_price = order.type == OrderType::LIMIT ? order.price : 1000000.0;
        double freeze_amount = order.volume * estimate_price * 1.003;
        account_.unfreeze_cash(freeze_amount);
    } else {
        account_.unfreeze_position(order.symbol, order.volume);
    }
    
    // 更新订单状态
    order.status = OrderStatus::CANCELLED;
    order.cancel_time = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
    
    return true;
}

// ============================================================================
// 查询方法
// ============================================================================

SimulatedOrder SimulatedExchange::get_order(const std::string& order_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = orders_.find(order_id);
    if (it != orders_.end()) {
        return it->second;
    }
    
    return SimulatedOrder();
}

std::vector<SimulatedOrder> SimulatedExchange::get_pending_orders() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<SimulatedOrder> result;
    for (const auto& pair : orders_) {
        if (pair.second.status == OrderStatus::PENDING) {
            result.push_back(pair.second);
        }
    }
    
    return result;
}

std::vector<SimulatedOrder> SimulatedExchange::get_pending_orders(const std::string& symbol) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<SimulatedOrder> result;
    for (const auto& pair : orders_) {
        if (pair.second.status == OrderStatus::PENDING && pair.second.symbol == symbol) {
            result.push_back(pair.second);
        }
    }
    
    return result;
}

std::vector<TradeRecord> SimulatedExchange::get_trade_history() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return trade_history_;
}

Position SimulatedExchange::get_position(const std::string& symbol) const {
    return account_.get_position(symbol);
}

std::vector<Position> SimulatedExchange::get_all_positions() const {
    return account_.get_all_positions();
}

double SimulatedExchange::get_total_assets() const {
    return account_.get_total_assets();
}

double SimulatedExchange::get_available_cash() const {
    return account_.get_available_cash();
}

double SimulatedExchange::get_frozen_cash() const {
    return account_.get_frozen_cash();
}

// ============================================================================
// 日常维护
// ============================================================================

void SimulatedExchange::update_daily(int64_t current_date) {
    std::lock_guard<std::mutex> lock(mutex_);
    account_.update_available_volume(current_date);
}

std::string SimulatedExchange::get_account_id() const {
    return account_.get_account_id();
}

// ============================================================================
// 私有方法
// ============================================================================

std::string SimulatedExchange::generate_order_id(const std::string& symbol) {
    // 格式：ORDER_{timestamp}_{symbol}_{counter}
    order_counter_++;
    
    auto now = std::chrono::system_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()
    ).count();
    
    std::stringstream ss;
    ss << "ORDER_" << ms << "_" << symbol << "_" << order_counter_;
    
    return ss.str();
}

void SimulatedExchange::process_fill(
    SimulatedOrder& order,
    const MatchResult& match_result,
    int64_t current_date
) {
    // 1. 计算手续费
    double commission = calculate_commission(
        order.side,
        match_result.filled_price,
        match_result.filled_volume
    );
    
    // 2. 更新账户
    double realized_pnl = 0.0;
    
    if (order.side == OrderSide::BUY) {
        // 买入：增加持仓，扣除实际花费
        double actual_cost = match_result.filled_volume * match_result.filled_price + commission;
        
        // 解冻预冻结的资金
        double estimate_price = order.type == OrderType::LIMIT ? order.price : 1000000.0;
        double freeze_amount = order.volume * estimate_price * 1.003;
        account_.unfreeze_cash(freeze_amount);
        
        // 扣除实际花费
        if (!account_.freeze_cash(actual_cost)) {
            // 理论上不应该失败，因为已经冻结了更多的钱
            process_reject(order, "Insufficient cash after fill");
            return;
        }
        account_.unfreeze_cash(actual_cost);  // 立即解冻（相当于直接扣除）
        
        // 增加持仓
        account_.add_position(order.symbol, match_result.filled_volume, 
                             match_result.filled_price, current_date);
        
    } else {
        // 卖出：减少持仓，增加资金
        if (!account_.reduce_position(order.symbol, match_result.filled_volume,
                                      match_result.filled_price, realized_pnl)) {
            process_reject(order, "Failed to reduce position");
            return;
        }
        
        // 扣除手续费
        account_.freeze_cash(commission);
        account_.unfreeze_cash(commission);
        
        // 解冻持仓
        account_.unfreeze_position(order.symbol, match_result.filled_volume);
    }
    
    // 3. 更新订单状态
    order.status = OrderStatus::FILLED;
    order.filled_volume = match_result.filled_volume;
    order.filled_time = current_time_;
    
    // 4. 生成成交记录
    TradeRecord trade;
    trade.trade_id = "TRADE_" + std::to_string(current_time_) + "_" + std::to_string(trade_history_.size() + 1);
    trade.order_id = order.order_id;
    trade.symbol = order.symbol;
    trade.side = order.side;
    trade.price = match_result.filled_price;
    trade.volume = match_result.filled_volume;
    trade.commission = commission;
    trade.trade_time = current_time_;
    trade.realized_pnl = realized_pnl;
    
    trade_history_.push_back(trade);
}

void SimulatedExchange::process_reject(
    SimulatedOrder& order,
    const std::string& reason
) {
    // 1. 解冻资金或持仓
    if (order.side == OrderSide::BUY) {
        double estimate_price = order.type == OrderType::LIMIT ? order.price : 1000000.0;
        double freeze_amount = order.volume * estimate_price * 1.003;
        account_.unfreeze_cash(freeze_amount);
    } else {
        account_.unfreeze_position(order.symbol, order.volume);
    }
    
    // 2. 更新订单状态
    order.status = OrderStatus::REJECTED;
}

double SimulatedExchange::calculate_commission(
    OrderSide side,
    double filled_price,
    int64_t filled_volume
) {
    double turnover = filled_price * filled_volume;
    
    // 手续费率：万2.5
    double commission = turnover * 0.00025;
    
    // 最低5元
    commission = std::max(commission, 5.0);
    
    // 卖出还需加印花税：千一
    if (side == OrderSide::SELL) {
        double stamp_tax = turnover * 0.001;
        commission += stamp_tax;
    }
    
    return std::round(commission * 100.0) / 100.0;
}

} // namespace simulation
} // namespace apexquant
