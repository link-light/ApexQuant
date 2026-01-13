#include "backtest_engine.h"
#include <cmath>
#include <algorithm>
#include <numeric>

namespace apexquant {

BacktestEngine::BacktestEngine(const BacktestConfig& config)
    : config_(config), cash_(config.initial_capital), initial_cash_(config.initial_capital) {
}

void BacktestEngine::set_data(const std::vector<Bar>& bars) {
    data_ = bars;
}

void BacktestEngine::set_on_bar_callback(OnBarCallback callback) {
    on_bar_callback_ = callback;
}

BacktestResult BacktestEngine::run() {
    // 重置状态
    cash_ = initial_cash_;
    positions_.clear();
    pending_orders_.clear();
    trades_.clear();
    equity_curve_.clear();
    timestamps_.clear();
    
    // 遍历所有 Bar
    for (const auto& bar : data_) {
        process_bar(bar);
    }
    
    // 计算回测结果
    BacktestResult result;
    result.trades = trades_;
    result.equity_curve = equity_curve_;
    result.total_trades = static_cast<int>(trades_.size());
    
    // 总手续费和滑点
    for (const auto& trade : trades_) {
        result.total_commission += trade.commission;
        result.total_slippage += trade.slippage;
    }
    
    // 计算收益率
    if (!equity_curve_.empty() && initial_cash_ > 0) {
        double final_value = equity_curve_.back();
        result.total_return = (final_value - initial_cash_) / initial_cash_;
        
        // 年化收益率（假设 252 个交易日）
        if (data_.size() > 0) {
            double days = static_cast<double>(data_.size());
            double years = days / 252.0;
            if (years > 0) {
                result.annual_return = std::pow(1.0 + result.total_return, 1.0 / years) - 1.0;
            }
        }
    }
    
    // 计算日收益率和夏普比率
    if (equity_curve_.size() > 1) {
        result.daily_returns.reserve(equity_curve_.size() - 1);
        for (size_t i = 1; i < equity_curve_.size(); ++i) {
            double ret = (equity_curve_[i] - equity_curve_[i-1]) / equity_curve_[i-1];
            result.daily_returns.push_back(ret);
        }
        
        // 夏普比率
        if (!result.daily_returns.empty()) {
            double mean_return = std::accumulate(result.daily_returns.begin(), 
                                                result.daily_returns.end(), 0.0) / result.daily_returns.size();
            double variance = 0.0;
            for (double ret : result.daily_returns) {
                variance += (ret - mean_return) * (ret - mean_return);
            }
            double std_dev = std::sqrt(variance / result.daily_returns.size());
            
            if (std_dev > 0) {
                result.sharpe_ratio = (mean_return / std_dev) * std::sqrt(252.0);
            }
        }
    }
    
    // 计算最大回撤
    if (!equity_curve_.empty()) {
        double peak = equity_curve_[0];
        double max_dd = 0.0;
        
        for (double value : equity_curve_) {
            if (value > peak) {
                peak = value;
            }
            double drawdown = (peak - value) / peak;
            max_dd = std::max(max_dd, drawdown);
        }
        
        result.max_drawdown = max_dd;
    }
    
    // 胜率统计
    for (size_t i = 1; i < trades_.size(); ++i) {
        const auto& prev_trade = trades_[i-1];
        const auto& curr_trade = trades_[i];
        
        // 简化：如果是一对买卖，计算盈亏
        if (prev_trade.side == OrderSide::BUY && curr_trade.side == OrderSide::SELL) {
            double pnl = (curr_trade.price - prev_trade.price) * prev_trade.quantity
                        - prev_trade.commission - curr_trade.commission
                        - prev_trade.slippage - curr_trade.slippage;
            
            if (pnl > 0) {
                result.winning_trades++;
            } else if (pnl < 0) {
                result.losing_trades++;
            }
        }
    }
    
    int total_pairs = result.winning_trades + result.losing_trades;
    if (total_pairs > 0) {
        result.win_rate = static_cast<double>(result.winning_trades) / total_pairs;
    }
    
    return result;
}

void BacktestEngine::process_bar(const Bar& bar) {
    current_bar_ = bar;
    
    // 更新持仓市值
    update_positions(bar);
    
    // 执行待处理订单
    for (auto& order : pending_orders_) {
        if (order.symbol == bar.symbol) {
            execute_order(order, bar);
        }
    }
    pending_orders_.clear();
    
    // 记录权益
    record_equity();
    
    // 调用策略回调
    if (on_bar_callback_) {
        on_bar_callback_(bar);
    }
}

void BacktestEngine::execute_order(const Order& order, const Bar& bar) {
    double exec_price = 0.0;
    
    // 确定成交价格
    if (order.type == OrderType::MARKET) {
        exec_price = bar.close;  // 简化：使用收盘价
    } else if (order.type == OrderType::LIMIT) {
        // 限价单逻辑
        if (order.side == OrderSide::BUY && order.price >= bar.low) {
            exec_price = std::min(order.price, bar.close);
        } else if (order.side == OrderSide::SELL && order.price <= bar.high) {
            exec_price = std::max(order.price, bar.close);
        } else {
            return;  // 不满足成交条件
        }
    }
    
    // 计算滑点
    double slippage = calculate_slippage(exec_price, order.quantity, order.side);
    if (order.side == OrderSide::BUY) {
        exec_price += slippage / order.quantity;
    } else {
        exec_price -= slippage / order.quantity;
    }
    
    double total_value = exec_price * order.quantity;
    double commission = calculate_commission(total_value);
    
    // 检查资金
    if (order.side == OrderSide::BUY) {
        double required = total_value + commission;
        if (required > cash_) {
            return;  // 资金不足
        }
        
        cash_ -= required;
        
        // 更新或创建持仓
        auto& pos = positions_[order.symbol];
        if (pos.quantity == 0) {
            pos.symbol = order.symbol;
            pos.quantity = order.quantity;
            pos.avg_price = exec_price;
        } else {
            double total_cost = pos.avg_price * pos.quantity + exec_price * order.quantity;
            pos.quantity += order.quantity;
            pos.avg_price = total_cost / pos.quantity;
        }
    } else {  // SELL
        auto it = positions_.find(order.symbol);
        if (it == positions_.end() || it->second.quantity < order.quantity) {
            return;  // 持仓不足
        }
        
        cash_ += total_value - commission;
        
        // 更新持仓
        auto& pos = it->second;
        pos.quantity -= order.quantity;
        
        // 计算已实现盈亏
        double pnl = (exec_price - pos.avg_price) * order.quantity - commission;
        pos.realized_pnl += pnl;
        
        if (pos.quantity == 0) {
            positions_.erase(it);
        }
    }
    
    // 记录交易
    Trade trade;
    trade.symbol = order.symbol;
    trade.timestamp = bar.timestamp;
    trade.side = order.side;
    trade.quantity = order.quantity;
    trade.price = exec_price;
    trade.commission = commission;
    trade.slippage = slippage;
    trade.strategy_id = order.strategy_id;
    
    trades_.push_back(trade);
}

double BacktestEngine::calculate_commission(double value) const {
    double commission = value * config_.commission_rate;
    return std::max(commission, config_.min_commission);
}

double BacktestEngine::calculate_slippage(double price, int64_t quantity, OrderSide side) const {
    double slippage = price * quantity * config_.slippage_rate;
    
    // 冲击成本（简化模型）
    if (config_.enable_market_impact) {
        double impact = price * std::sqrt(static_cast<double>(quantity)) * config_.market_impact_coef;
        slippage += impact;
    }
    
    return slippage;
}

void BacktestEngine::update_positions(const Bar& bar) {
    for (auto& [symbol, pos] : positions_) {
        if (symbol == bar.symbol) {
            pos.update_market_value(bar.close);
        }
    }
}

void BacktestEngine::record_equity() {
    double total_value = get_total_value();
    equity_curve_.push_back(total_value);
    timestamps_.push_back(current_bar_.timestamp);
}

double BacktestEngine::get_total_value() const {
    double total = cash_;
    for (const auto& [symbol, pos] : positions_) {
        total += pos.market_value;
    }
    return total;
}

Position BacktestEngine::get_position(const std::string& symbol) const {
    auto it = positions_.find(symbol);
    if (it != positions_.end()) {
        return it->second;
    }
    return Position();
}

bool BacktestEngine::has_position(const std::string& symbol) const {
    auto it = positions_.find(symbol);
    return it != positions_.end() && it->second.quantity > 0;
}

void BacktestEngine::buy(const std::string& symbol, int64_t quantity, double limit_price) {
    Order order;
    order.symbol = symbol;
    order.side = OrderSide::BUY;
    order.quantity = quantity;
    order.type = (limit_price > 0) ? OrderType::LIMIT : OrderType::MARKET;
    order.price = limit_price;
    order.status = OrderStatus::PENDING;
    
    pending_orders_.push_back(order);
}

void BacktestEngine::sell(const std::string& symbol, int64_t quantity, double limit_price) {
    Order order;
    order.symbol = symbol;
    order.side = OrderSide::SELL;
    order.quantity = quantity;
    order.type = (limit_price > 0) ? OrderType::LIMIT : OrderType::MARKET;
    order.price = limit_price;
    order.status = OrderStatus::PENDING;
    
    pending_orders_.push_back(order);
}

void BacktestEngine::close_position(const std::string& symbol) {
    auto it = positions_.find(symbol);
    if (it != positions_.end() && it->second.quantity > 0) {
        sell(symbol, it->second.quantity);
    }
}

} // namespace apexquant

