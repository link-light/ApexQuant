/**
 * @file simulation_account.cpp
 * @brief ApexQuant模拟账户管理类实现
 */

#include "simulation/simulation_account.h"
#include <cmath>
#include <algorithm>
#include <stdexcept>

namespace apexquant {
namespace simulation {

SimulationAccount::SimulationAccount(const std::string& account_id, double initial_capital)
    : account_id_(account_id),
      initial_capital_(initial_capital),
      available_cash_(initial_capital),
      withdrawable_cash_(initial_capital),
      frozen_cash_(0.0),
      today_sell_amount_(0.0),
      realized_pnl_(0.0) {
    
    if (initial_capital <= 0) {
        throw std::invalid_argument("Initial capital must be positive");
    }
}

// ============================================================================
// 资金管理
// ============================================================================

double SimulationAccount::get_total_assets() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // 总资产 = 可用现金 + 冻结资金 + 持仓市值
    double market_value = 0.0;
    for (const auto& pair : positions_) {
        market_value += pair.second.market_value;
    }
    
    return available_cash_ + frozen_cash_ + market_value;
}

double SimulationAccount::get_available_cash() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return available_cash_;
}

double SimulationAccount::get_withdrawable_cash() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return withdrawable_cash_;
}

double SimulationAccount::get_frozen_cash() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return frozen_cash_;
}

bool SimulationAccount::freeze_cash(double amount) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (amount < 0) {
        return false;
    }
    
    amount = round_to_cent(amount);
    
    if (available_cash_ < amount) {
        return false;  // 可用资金不足
    }
    
    available_cash_ -= amount;
    frozen_cash_ += amount;
    
    return true;
}

void SimulationAccount::unfreeze_cash(double amount) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (amount < 0) {
        return;
    }
    
    amount = round_to_cent(amount);
    amount = std::min(amount, frozen_cash_);  // 不能超过冻结金额
    
    frozen_cash_ -= amount;
    available_cash_ += amount;
}

// ============================================================================
// 持仓管理
// ============================================================================

bool SimulationAccount::add_position(
    const std::string& symbol, 
    int64_t volume, 
    double price, 
    int64_t buy_date
) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // 输入验证
    if (symbol.empty()) {
        return false;  // 股票代码不能为空
    }
    
    if (volume <= 0 || price <= 0) {
        return false;  // 数量和价格必须为正
    }
    
    if (volume > 1000000000) {  // 10亿股上限
        return false;  // 数量超过合理范围
    }
    
    if (price > 1000000.0) {  // 100万元/股上限
        return false;  // 价格超过合理范围
    }
    
    price = round_to_cent(price);
    double cost = round_to_cent(volume * price);
    
    auto it = positions_.find(symbol);
    if (it == positions_.end()) {
        // 新建持仓
        Position pos(symbol, volume, price, buy_date);
        pos.available_volume = 0;  // T+1，当天不可卖
        positions_[symbol] = pos;
    } else {
        // 加仓，更新平均成本
        Position& pos = it->second;
        double total_cost = pos.volume * pos.avg_cost + cost;
        pos.volume += volume;
        pos.avg_cost = round_to_cent(total_cost / pos.volume);
        pos.market_value = round_to_cent(pos.volume * pos.current_price);
        pos.unrealized_pnl = round_to_cent(pos.market_value - pos.volume * pos.avg_cost);
        
        // 新买入的部分T+1可卖，不更新buy_date（保持最早买入日期）
    }
    
    return true;
}

bool SimulationAccount::reduce_position(
    const std::string& symbol, 
    int64_t volume, 
    double sell_price, 
    double& realized_pnl
) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (volume <= 0 || sell_price <= 0) {
        return false;
    }
    
    auto it = positions_.find(symbol);
    if (it == positions_.end()) {
        return false;  // 没有持仓
    }
    
    Position& pos = it->second;
    
    if (pos.volume < volume) {
        return false;  // 持仓不足
    }
    
    sell_price = round_to_cent(sell_price);
    
    // 计算已实现盈亏
    double cost = round_to_cent(volume * pos.avg_cost);
    double revenue = round_to_cent(volume * sell_price);
    realized_pnl = round_to_cent(revenue - cost);
    realized_pnl_ += realized_pnl;
    
    // 增加可用资金（今日可用于买入）
    available_cash_ += revenue;
    
    // 记录今日卖出金额（明日才可取）
    today_sell_amount_ += revenue;
    
    // 减少持仓
    pos.volume -= volume;
    
    if (pos.volume == 0) {
        // 清仓
        positions_.erase(it);
    } else {
        // 更新市值和浮动盈亏
        pos.available_volume = std::max(int64_t(0), pos.available_volume - volume);
        pos.market_value = round_to_cent(pos.volume * pos.current_price);
        pos.unrealized_pnl = round_to_cent(pos.market_value - pos.volume * pos.avg_cost);
    }
    
    return true;
}

Position SimulationAccount::get_position(const std::string& symbol) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = positions_.find(symbol);
    if (it != positions_.end()) {
        return it->second;
    }
    
    return Position();  // 返回空持仓
}

std::vector<Position> SimulationAccount::get_all_positions() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::vector<Position> result;
    result.reserve(positions_.size());
    
    for (const auto& pair : positions_) {
        result.push_back(pair.second);
    }
    
    return result;
}

void SimulationAccount::update_position_price(const std::string& symbol, double current_price) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = positions_.find(symbol);
    if (it == positions_.end()) {
        return;
    }
    
    Position& pos = it->second;
    pos.current_price = round_to_cent(current_price);
    pos.market_value = round_to_cent(pos.volume * pos.current_price);
    pos.unrealized_pnl = round_to_cent(pos.market_value - pos.volume * pos.avg_cost);
}

// ============================================================================
// T+1相关
// ============================================================================

void SimulationAccount::update_available_volume(int64_t current_date) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    for (auto& pair : positions_) {
        Position& pos = pair.second;
        
        // 如果买入日期早于当前日期，全部可卖
        if (pos.buy_date < current_date) {
            pos.available_volume = pos.volume - pos.frozen_volume;
        }
    }
}

void SimulationAccount::daily_settlement(int64_t current_date) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // 1. 更新可取资金（昨日卖出的钱今日可取）
    // 简化处理：将可用资金同步到可取资金
    withdrawable_cash_ = available_cash_;
    
    // 2. 清零今日卖出金额（新的一天开始）
    today_sell_amount_ = 0.0;
    
    // 3. 更新持仓可卖数量（T+1解锁）
    for (auto& pair : positions_) {
        Position& pos = pair.second;
        
        // 如果买入日期早于当前日期，全部可卖
        if (pos.buy_date < current_date) {
            pos.available_volume = pos.volume - pos.frozen_volume;
        }
    }
}

bool SimulationAccount::can_sell(
    const std::string& symbol, 
    int64_t volume, 
    int64_t current_date
) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = positions_.find(symbol);
    if (it == positions_.end()) {
        return false;  // 没有持仓
    }
    
    const Position& pos = it->second;
    
    // T+1规则：当天买入不能当天卖出
    if (pos.buy_date == current_date) {
        return pos.available_volume >= volume;
    }
    
    // 检查可卖数量
    return (pos.volume - pos.frozen_volume) >= volume;
}

bool SimulationAccount::freeze_position(const std::string& symbol, int64_t volume) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (volume <= 0) {
        return false;
    }
    
    auto it = positions_.find(symbol);
    if (it == positions_.end()) {
        return false;
    }
    
    Position& pos = it->second;
    
    // 检查是否有足够的可用持仓
    int64_t available = pos.volume - pos.frozen_volume;
    if (available < volume) {
        return false;
    }
    
    pos.frozen_volume += volume;
    return true;
}

void SimulationAccount::unfreeze_position(const std::string& symbol, int64_t volume) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (volume <= 0) {
        return;
    }
    
    auto it = positions_.find(symbol);
    if (it == positions_.end()) {
        return;
    }
    
    Position& pos = it->second;
    pos.frozen_volume = std::max(int64_t(0), pos.frozen_volume - volume);
}

// ============================================================================
// 绩效统计
// ============================================================================

double SimulationAccount::get_total_pnl() const {
    return realized_pnl_ + get_unrealized_pnl();
}

double SimulationAccount::get_unrealized_pnl() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    double total_unrealized = 0.0;
    for (const auto& pair : positions_) {
        total_unrealized += pair.second.unrealized_pnl;
    }
    
    return round_to_cent(total_unrealized);
}

double SimulationAccount::get_realized_pnl() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return realized_pnl_;
}

// ============================================================================
// 辅助方法
// ============================================================================

double SimulationAccount::round_to_cent(double value) const {
    return std::round(value * 100.0) / 100.0;
}

} // namespace simulation
} // namespace apexquant
