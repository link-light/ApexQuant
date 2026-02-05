/**
 * @file simulation_types.h
 * @brief ApexQuant模拟盘核心数据结构定义
 * 
 * 包含订单、持仓、成交等核心数据结构
 * C++17标准
 */

#ifndef APEXQUANT_SIMULATION_TYPES_H
#define APEXQUANT_SIMULATION_TYPES_H

#include <string>
#include <cstdint>
#include <sstream>
#include <iomanip>

namespace apexquant {
namespace simulation {

// ============================================================================
// 枚举类型定义
// ============================================================================

/**
 * @brief 订单方向
 */
enum class OrderSide : int {
    BUY = 0,   // 买入
    SELL = 1   // 卖出
};

/**
 * @brief 订单类型
 */
enum class OrderType : int {
    MARKET = 0,  // 市价单
    LIMIT = 1    // 限价单
};

/**
 * @brief 订单状态
 */
enum class OrderStatus : int {
    PENDING = 0,         // 待成交
    PARTIAL_FILLED = 1,  // 部分成交
    FILLED = 2,          // 完全成交
    CANCELLED = 3,       // 已撤销
    REJECTED = 4         // 已拒绝
};

// ============================================================================
// 辅助函数：枚举转字符串
// ============================================================================

inline std::string orderSideToString(OrderSide side) {
    switch (side) {
        case OrderSide::BUY: return "BUY";
        case OrderSide::SELL: return "SELL";
        default: return "UNKNOWN";
    }
}

inline std::string orderTypeToString(OrderType type) {
    switch (type) {
        case OrderType::MARKET: return "MARKET";
        case OrderType::LIMIT: return "LIMIT";
        default: return "UNKNOWN";
    }
}

inline std::string orderStatusToString(OrderStatus status) {
    switch (status) {
        case OrderStatus::PENDING: return "PENDING";
        case OrderStatus::PARTIAL_FILLED: return "PARTIAL_FILLED";
        case OrderStatus::FILLED: return "FILLED";
        case OrderStatus::CANCELLED: return "CANCELLED";
        case OrderStatus::REJECTED: return "REJECTED";
        default: return "UNKNOWN";
    }
}

// ============================================================================
// 结构体定义
// ============================================================================

/**
 * @brief 模拟订单
 */
struct SimulatedOrder {
    std::string order_id;           // 订单ID
    std::string symbol;             // 股票代码
    OrderSide side;                 // 买卖方向
    OrderType type;                 // 订单类型
    double price;                   // 价格（限价单使用，市价单为0）
    int64_t volume;                 // 委托数量
    int64_t filled_volume;          // 已成交数量
    OrderStatus status;             // 订单状态
    int64_t submit_time;            // 提交时间（Unix毫秒时间戳）
    int64_t cancel_time;            // 撤销时间（0表示未撤销）
    int64_t filled_time;            // 成交时间（0表示未成交）
    double commission_rate;         // 手续费率
    double slippage_rate;           // 滑点率
    
    // 默认构造函数
    SimulatedOrder()
        : order_id(""),
          symbol(""),
          side(OrderSide::BUY),
          type(OrderType::MARKET),
          price(0.0),
          volume(0),
          filled_volume(0),
          status(OrderStatus::PENDING),
          submit_time(0),
          cancel_time(0),
          filled_time(0),
          commission_rate(0.00025),   // 默认万2.5
          slippage_rate(0.0001) {}    // 默认万一
    
    // 带参数构造函数
    SimulatedOrder(
        const std::string& id,
        const std::string& sym,
        OrderSide s,
        OrderType t,
        double p,
        int64_t v,
        int64_t st
    ) : order_id(id),
        symbol(sym),
        side(s),
        type(t),
        price(p),
        volume(v),
        filled_volume(0),
        status(OrderStatus::PENDING),
        submit_time(st),
        cancel_time(0),
        filled_time(0),
        commission_rate(0.00025),
        slippage_rate(0.0001) {}
    
    // 转字符串用于调试
    std::string toString() const {
        std::stringstream ss;
        ss << std::fixed << std::setprecision(2);
        ss << "Order{id=" << order_id
           << ", symbol=" << symbol
           << ", side=" << orderSideToString(side)
           << ", type=" << orderTypeToString(type)
           << ", price=" << price
           << ", volume=" << volume
           << ", filled=" << filled_volume
           << ", status=" << orderStatusToString(status)
           << "}";
        return ss.str();
    }
};

/**
 * @brief 持仓信息
 */
struct Position {
    std::string symbol;             // 股票代码
    int64_t volume;                 // 总持仓数量
    int64_t available_volume;       // 可卖数量（T+1）
    int64_t frozen_volume;          // 冻结数量（挂单中）
    double avg_cost;                // 平均成本
    double current_price;           // 当前价格
    double market_value;            // 市值
    double unrealized_pnl;          // 浮动盈亏
    int64_t buy_date;               // 买入日期（用于T+1判断，格式：20250203）
    
    // 默认构造函数
    Position()
        : symbol(""),
          volume(0),
          available_volume(0),
          frozen_volume(0),
          avg_cost(0.0),
          current_price(0.0),
          market_value(0.0),
          unrealized_pnl(0.0),
          buy_date(0) {}
    
    // 带参数构造函数
    Position(
        const std::string& sym,
        int64_t vol,
        double cost,
        int64_t date
    ) : symbol(sym),
        volume(vol),
        available_volume(0),         // 新买入的T+1可卖
        frozen_volume(0),
        avg_cost(cost),
        current_price(cost),
        market_value(vol * cost),
        unrealized_pnl(0.0),
        buy_date(date) {}
    
    // 转字符串
    std::string toString() const {
        std::stringstream ss;
        ss << std::fixed << std::setprecision(2);
        ss << "Position{symbol=" << symbol
           << ", volume=" << volume
           << ", available=" << available_volume
           << ", frozen=" << frozen_volume
           << ", cost=" << avg_cost
           << ", price=" << current_price
           << ", value=" << market_value
           << ", pnl=" << unrealized_pnl
           << "}";
        return ss.str();
    }
};

/**
 * @brief 成交记录
 */
struct TradeRecord {
    std::string trade_id;           // 成交ID
    std::string order_id;           // 关联订单ID
    std::string symbol;             // 股票代码
    OrderSide side;                 // 买卖方向
    double price;                   // 成交价格
    int64_t volume;                 // 成交数量
    double commission;              // 手续费
    int64_t trade_time;             // 成交时间（Unix毫秒时间戳）
    double realized_pnl;            // 已实现盈亏（仅卖出有效）
    
    // 默认构造函数
    TradeRecord()
        : trade_id(""),
          order_id(""),
          symbol(""),
          side(OrderSide::BUY),
          price(0.0),
          volume(0),
          commission(0.0),
          trade_time(0),
          realized_pnl(0.0) {}
    
    // 带参数构造函数
    TradeRecord(
        const std::string& tid,
        const std::string& oid,
        const std::string& sym,
        OrderSide s,
        double p,
        int64_t v,
        double c,
        int64_t tt
    ) : trade_id(tid),
        order_id(oid),
        symbol(sym),
        side(s),
        price(p),
        volume(v),
        commission(c),
        trade_time(tt),
        realized_pnl(0.0) {}
    
    // 转字符串
    std::string toString() const {
        std::stringstream ss;
        ss << std::fixed << std::setprecision(2);
        ss << "Trade{id=" << trade_id
           << ", order=" << order_id
           << ", symbol=" << symbol
           << ", side=" << orderSideToString(side)
           << ", price=" << price
           << ", volume=" << volume
           << ", commission=" << commission
           << ", pnl=" << realized_pnl
           << "}";
        return ss.str();
    }
};

/**
 * @brief 撮合结果
 */
struct MatchResult {
    bool success;                   // 是否成交
    double filled_price;            // 成交价格
    int64_t filled_volume;          // 成交数量
    std::string reject_reason;      // 拒绝原因
    
    // 默认构造函数
    MatchResult()
        : success(false),
          filled_price(0.0),
          filled_volume(0),
          reject_reason("") {}
    
    // 成功构造函数
    MatchResult(double price, int64_t volume)
        : success(true),
          filled_price(price),
          filled_volume(volume),
          reject_reason("") {}
    
    // 失败构造函数
    explicit MatchResult(const std::string& reason)
        : success(false),
          filled_price(0.0),
          filled_volume(0),
          reject_reason(reason) {}
    
    // 转字符串
    std::string toString() const {
        if (success) {
            std::stringstream ss;
            ss << std::fixed << std::setprecision(2);
            ss << "Match{success=true, price=" << filled_price
               << ", volume=" << filled_volume << "}";
            return ss.str();
        } else {
            return "Match{success=false, reason=" + reject_reason + "}";
        }
    }
};

} // namespace simulation
} // namespace apexquant

#endif // APEXQUANT_SIMULATION_TYPES_H
