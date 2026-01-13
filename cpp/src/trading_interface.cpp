#include "trading_interface.h"
#include <chrono>
#include <iomanip>
#include <sstream>
#include <ctime>

namespace apexquant {
namespace trading {

// ==================== SimulatedTrading 实现 ====================

SimulatedTrading::SimulatedTrading()
    : connected_(false),
      logged_in_(false),
      next_order_id_(1),
      next_trade_id_(1) {
    account_.available_cash = 100000.0;  // 默认 10 万初始资金
    account_.total_assets = 100000.0;
}

bool SimulatedTrading::connect(const std::string& config) {
    connected_ = true;
    return true;
}

void SimulatedTrading::disconnect() {
    connected_ = false;
    logged_in_ = false;
}

bool SimulatedTrading::is_connected() const {
    return connected_;
}

bool SimulatedTrading::login(const std::string& username, const std::string& password) {
    if (!connected_) return false;
    logged_in_ = true;
    return true;
}

std::string SimulatedTrading::submit_order(const TradeOrder& order) {
    if (!logged_in_) {
        if (error_callback_) {
            error_callback_("未登录");
        }
        return "";
    }
    
    TradeOrder new_order = order;
    new_order.order_id = generate_order_id();
    new_order.status = OrderStatus::SUBMITTED;
    
    // 获取当前时间
    auto now = std::chrono::system_clock::now();
    auto time_t_now = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t_now), "%Y-%m-%d %H:%M:%S");
    new_order.submit_time = ss.str();
    new_order.update_time = ss.str();
    
    // 检查资金/持仓
    if (new_order.direction == OrderDirection::BUY) {
        double required_cash = new_order.price * new_order.volume * 1.0003;  // 含手续费
        if (required_cash > account_.available_cash) {
            new_order.status = OrderStatus::REJECTED;
            new_order.message = "资金不足";
            if (error_callback_) {
                error_callback_("资金不足");
            }
            orders_[new_order.order_id] = new_order;
            return new_order.order_id;
        }
        // 冻结资金
        account_.available_cash -= required_cash;
        account_.frozen_cash += required_cash;
    } else {
        auto it = positions_.find(new_order.symbol);
        if (it == positions_.end() || it->second.available_volume < new_order.volume) {
            new_order.status = OrderStatus::REJECTED;
            new_order.message = "持仓不足";
            if (error_callback_) {
                error_callback_("持仓不足");
            }
            orders_[new_order.order_id] = new_order;
            return new_order.order_id;
        }
        // 冻结持仓
        it->second.available_volume -= new_order.volume;
        it->second.frozen_volume += new_order.volume;
    }
    
    orders_[new_order.order_id] = new_order;
    
    if (order_callback_) {
        order_callback_(new_order);
    }
    
    // 市价单立即执行
    if (new_order.type == OrderType::MARKET) {
        execute_order(orders_[new_order.order_id]);
    }
    
    return new_order.order_id;
}

bool SimulatedTrading::cancel_order(const std::string& order_id) {
    auto it = orders_.find(order_id);
    if (it == orders_.end()) {
        return false;
    }
    
    TradeOrder& order = it->second;
    if (order.status != OrderStatus::SUBMITTED && order.status != OrderStatus::PARTIAL) {
        return false;
    }
    
    order.status = OrderStatus::CANCELLED;
    
    // 解冻资金/持仓
    int remaining_volume = order.volume - order.filled_volume;
    if (order.direction == OrderDirection::BUY) {
        double unfrozen_cash = order.price * remaining_volume * 1.0003;
        account_.frozen_cash -= unfrozen_cash;
        account_.available_cash += unfrozen_cash;
    } else {
        auto pos_it = positions_.find(order.symbol);
        if (pos_it != positions_.end()) {
            pos_it->second.frozen_volume -= remaining_volume;
            pos_it->second.available_volume += remaining_volume;
        }
    }
    
    if (order_callback_) {
        order_callback_(order);
    }
    
    return true;
}

TradeOrder SimulatedTrading::query_order(const std::string& order_id) {
    auto it = orders_.find(order_id);
    if (it != orders_.end()) {
        return it->second;
    }
    return TradeOrder();
}

std::vector<TradeOrder> SimulatedTrading::query_orders(const std::string& symbol) {
    std::vector<TradeOrder> result;
    for (const auto& pair : orders_) {
        if (symbol.empty() || pair.second.symbol == symbol) {
            result.push_back(pair.second);
        }
    }
    return result;
}

AccountInfo SimulatedTrading::query_account() {
    update_account();
    return account_;
}

std::vector<PositionInfo> SimulatedTrading::query_positions() {
    std::vector<PositionInfo> result;
    for (const auto& pair : positions_) {
        if (pair.second.total_volume > 0) {
            result.push_back(pair.second);
        }
    }
    return result;
}

PositionInfo SimulatedTrading::query_position(const std::string& symbol) {
    auto it = positions_.find(symbol);
    if (it != positions_.end()) {
        return it->second;
    }
    return PositionInfo();
}

std::vector<TradeReport> SimulatedTrading::query_trades() {
    return trades_;
}

void SimulatedTrading::set_order_callback(std::function<void(const TradeOrder&)> callback) {
    order_callback_ = callback;
}

void SimulatedTrading::set_trade_callback(std::function<void(const TradeReport&)> callback) {
    trade_callback_ = callback;
}

void SimulatedTrading::set_error_callback(std::function<void(const std::string&)> callback) {
    error_callback_ = callback;
}

void SimulatedTrading::set_initial_cash(double cash) {
    account_.available_cash = cash;
    account_.total_assets = cash;
}

void SimulatedTrading::update_market_price(const std::string& symbol, double price) {
    market_prices_[symbol] = price;
    
    // 更新持仓市值
    auto it = positions_.find(symbol);
    if (it != positions_.end()) {
        it->second.current_price = price;
        it->second.market_value = price * it->second.total_volume;
        it->second.profit_loss = (price - it->second.avg_price) * it->second.total_volume;
        it->second.profit_loss_ratio = it->second.profit_loss / (it->second.avg_price * it->second.total_volume);
    }
}

void SimulatedTrading::process_orders() {
    for (auto& pair : orders_) {
        TradeOrder& order = pair.second;
        if (order.status == OrderStatus::SUBMITTED || order.status == OrderStatus::PARTIAL) {
            execute_order(order);
        }
    }
}

void SimulatedTrading::execute_order(TradeOrder& order) {
    // 获取市场价格
    double execute_price = order.price;
    if (order.type == OrderType::MARKET) {
        auto it = market_prices_.find(order.symbol);
        if (it != market_prices_.end()) {
            execute_price = it->second;
        } else {
            order.status = OrderStatus::REJECTED;
            order.message = "无市场价格";
            return;
        }
    }
    
    // 限价单检查价格
    if (order.type == OrderType::LIMIT) {
        auto it = market_prices_.find(order.symbol);
        if (it != market_prices_.end()) {
            double market_price = it->second;
            if (order.direction == OrderDirection::BUY && market_price > order.price) {
                return;  // 买入价格高于限价，不成交
            }
            if (order.direction == OrderDirection::SELL && market_price < order.price) {
                return;  // 卖出价格低于限价，不成交
            }
            execute_price = market_price;
        }
    }
    
    // 生成成交
    TradeReport trade;
    trade.trade_id = generate_trade_id();
    trade.order_id = order.order_id;
    trade.symbol = order.symbol;
    trade.direction = order.direction;
    trade.price = execute_price;
    trade.volume = order.volume - order.filled_volume;
    trade.commission = execute_price * trade.volume * 0.0003;
    
    auto now = std::chrono::system_clock::now();
    auto time_t_now = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t_now), "%Y-%m-%d %H:%M:%S");
    trade.trade_time = ss.str();
    
    trades_.push_back(trade);
    
    // 更新订单
    order.filled_volume += trade.volume;
    order.avg_filled_price = ((order.avg_filled_price * (order.filled_volume - trade.volume)) +
                              (execute_price * trade.volume)) / order.filled_volume;
    order.status = OrderStatus::FILLED;
    order.update_time = trade.trade_time;
    
    // 更新持仓
    update_position(trade);
    
    // 回调
    if (trade_callback_) {
        trade_callback_(trade);
    }
    if (order_callback_) {
        order_callback_(order);
    }
}

void SimulatedTrading::update_position(const TradeReport& trade) {
    PositionInfo& pos = positions_[trade.symbol];
    pos.symbol = trade.symbol;
    
    if (trade.direction == OrderDirection::BUY) {
        // 买入
        double total_cost = pos.avg_price * pos.total_volume + trade.price * trade.volume;
        pos.total_volume += trade.volume;
        pos.available_volume += trade.volume;
        pos.avg_price = total_cost / pos.total_volume;
        
        // 解冻资金
        double cost = trade.price * trade.volume + trade.commission;
        account_.frozen_cash -= (trade.price * trade.volume * 1.0003);
    } else {
        // 卖出
        pos.total_volume -= trade.volume;
        pos.frozen_volume -= trade.volume;
        
        // 回收资金
        double proceeds = trade.price * trade.volume - trade.commission;
        account_.available_cash += proceeds;
        
        if (pos.total_volume == 0) {
            positions_.erase(trade.symbol);
        }
    }
    
    update_account();
}

void SimulatedTrading::update_account() {
    double market_value = 0.0;
    for (const auto& pair : positions_) {
        market_value += pair.second.market_value;
    }
    
    account_.market_value = market_value;
    account_.total_assets = account_.available_cash + account_.frozen_cash + market_value;
    account_.profit_loss = account_.total_assets - 100000.0;  // 假设初始资金 10 万
}

std::string SimulatedTrading::generate_order_id() {
    return "ORD" + std::to_string(next_order_id_++);
}

std::string SimulatedTrading::generate_trade_id() {
    return "TRD" + std::to_string(next_trade_id_++);
}

} // namespace trading
} // namespace apexquant

