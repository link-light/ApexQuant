#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <iostream>

namespace apexquant {

/**
 * @brief Tick 行情数据结构
 * 表示最细粒度的市场快照数据
 */
struct Tick {
    std::string symbol;        // 证券代码，如 "600519.SH"
    int64_t timestamp;         // 时间戳（毫秒）
    double last_price;         // 最新价
    double bid_price;          // 买一价
    double ask_price;          // 卖一价
    int64_t volume;           // 成交量
    double amount;            // 成交额
    
    // 五档行情（可选扩展）
    std::vector<double> bid_prices;   // 买价列表
    std::vector<int64_t> bid_volumes; // 买量列表
    std::vector<double> ask_prices;   // 卖价列表
    std::vector<int64_t> ask_volumes; // 卖量列表
    
    Tick() 
        : timestamp(0), last_price(0.0), bid_price(0.0), 
          ask_price(0.0), volume(0), amount(0.0) {}
    
    Tick(const std::string& sym, int64_t ts, double last, 
         double bid, double ask, int64_t vol)
        : symbol(sym), timestamp(ts), last_price(last),
          bid_price(bid), ask_price(ask), volume(vol), amount(0.0) {}
    
    // 获取中间价
    double mid_price() const {
        return (bid_price + ask_price) / 2.0;
    }
    
    // 获取买卖价差
    double spread() const {
        return ask_price - bid_price;
    }
};

/**
 * @brief Bar K线数据结构
 * 表示聚合后的时间周期数据（分钟、小时、日线等）
 */
struct Bar {
    std::string symbol;        // 证券代码
    int64_t timestamp;         // 时间戳（周期开始时间，毫秒）
    double open;              // 开盘价
    double high;              // 最高价
    double low;               // 最低价
    double close;             // 收盘价
    int64_t volume;           // 成交量
    double amount;            // 成交额
    int64_t trade_count;      // 成交笔数（可选）
    
    Bar() 
        : timestamp(0), open(0.0), high(0.0), low(0.0), 
          close(0.0), volume(0), amount(0.0), trade_count(0) {}
    
    Bar(const std::string& sym, int64_t ts, double o, double h, 
        double l, double c, int64_t vol)
        : symbol(sym), timestamp(ts), open(o), high(h), low(l), 
          close(c), volume(vol), amount(0.0), trade_count(0) {}
    
    // 获取涨跌幅
    double change_rate() const {
        return open > 0 ? (close - open) / open : 0.0;
    }
    
    // 是否为阳线
    bool is_bullish() const {
        return close >= open;
    }
    
    // 实体大小
    double body_size() const {
        return std::abs(close - open);
    }
    
    // 上影线长度
    double upper_shadow() const {
        return high - std::max(open, close);
    }
    
    // 下影线长度
    double lower_shadow() const {
        return std::min(open, close) - low;
    }
};

/**
 * @brief Position 持仓数据结构
 */
struct Position {
    std::string symbol;        // 证券代码
    int64_t quantity;         // 持仓数量（正数为多头，负数为空头）
    double avg_price;         // 平均成本价
    double market_value;      // 市值
    double unrealized_pnl;    // 未实现盈亏
    double realized_pnl;      // 已实现盈亏
    int64_t open_timestamp;   // 开仓时间戳
    
    Position()
        : quantity(0), avg_price(0.0), market_value(0.0),
          unrealized_pnl(0.0), realized_pnl(0.0), open_timestamp(0) {}
    
    Position(const std::string& sym, int64_t qty, double avg_px)
        : symbol(sym), quantity(qty), avg_price(avg_px),
          market_value(0.0), unrealized_pnl(0.0), realized_pnl(0.0),
          open_timestamp(0) {}
    
    // 更新市值和未实现盈亏
    void update_market_value(double current_price) {
        market_value = quantity * current_price;
        unrealized_pnl = quantity * (current_price - avg_price);
    }
    
    // 是否为多头
    bool is_long() const {
        return quantity > 0;
    }
    
    // 是否为空头
    bool is_short() const {
        return quantity < 0;
    }
    
    // 是否为空仓
    bool is_flat() const {
        return quantity == 0;
    }
};

/**
 * @brief Order 订单数据结构
 */
enum class OrderSide {
    BUY,    // 买入
    SELL    // 卖出
};

enum class OrderType {
    MARKET,     // 市价单
    LIMIT,      // 限价单
    STOP,       // 止损单
    STOP_LIMIT  // 止损限价单
};

enum class OrderStatus {
    PENDING,        // 待提交
    SUBMITTED,      // 已提交
    PARTIAL_FILLED, // 部分成交
    FILLED,         // 完全成交
    CANCELLED,      // 已撤销
    REJECTED        // 已拒绝
};

struct Order {
    std::string order_id;      // 订单ID
    std::string symbol;        // 证券代码
    OrderSide side;           // 买卖方向
    OrderType type;           // 订单类型
    OrderStatus status;       // 订单状态
    
    int64_t quantity;         // 委托数量
    int64_t filled_quantity;  // 已成交数量
    double price;             // 委托价格（限价单）
    double filled_avg_price;  // 成交均价
    
    int64_t create_timestamp; // 创建时间
    int64_t update_timestamp; // 更新时间
    
    std::string strategy_id;  // 策略ID（用于追踪）
    std::string comment;      // 备注
    
    Order()
        : side(OrderSide::BUY), type(OrderType::MARKET), 
          status(OrderStatus::PENDING), quantity(0), 
          filled_quantity(0), price(0.0), filled_avg_price(0.0),
          create_timestamp(0), update_timestamp(0) {}
    
    Order(const std::string& sym, OrderSide sd, int64_t qty, double px = 0.0)
        : symbol(sym), side(sd), type(px > 0 ? OrderType::LIMIT : OrderType::MARKET),
          status(OrderStatus::PENDING), quantity(qty), filled_quantity(0),
          price(px), filled_avg_price(0.0), create_timestamp(0), update_timestamp(0) {}
    
    // 是否完全成交
    bool is_filled() const {
        return status == OrderStatus::FILLED;
    }
    
    // 是否活跃（可能继续成交）
    bool is_active() const {
        return status == OrderStatus::PENDING || 
               status == OrderStatus::SUBMITTED ||
               status == OrderStatus::PARTIAL_FILLED;
    }
    
    // 剩余数量
    int64_t remaining_quantity() const {
        return quantity - filled_quantity;
    }
    
    // 成交率
    double fill_ratio() const {
        return quantity > 0 ? static_cast<double>(filled_quantity) / quantity : 0.0;
    }
};

// 输出流操作符重载（用于调试）
inline std::ostream& operator<<(std::ostream& os, const Bar& bar) {
    os << "Bar(" << bar.symbol << ", " 
       << "O:" << bar.open << " H:" << bar.high 
       << " L:" << bar.low << " C:" << bar.close 
       << " V:" << bar.volume << ")";
    return os;
}

inline std::ostream& operator<<(std::ostream& os, const Position& pos) {
    os << "Position(" << pos.symbol << ", " 
       << "Qty:" << pos.quantity << " Avg:" << pos.avg_price 
       << " UnrealPnL:" << pos.unrealized_pnl << ")";
    return os;
}

} // namespace apexquant

