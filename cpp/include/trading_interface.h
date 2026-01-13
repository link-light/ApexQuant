#pragma once

#include <string>
#include <vector>
#include <functional>
#include <memory>
#include <map>
#include "data_structures.h"

namespace apexquant {
namespace trading {

// 订单状态
enum class OrderStatus {
    PENDING = 0,      // 待提交
    SUBMITTED = 1,    // 已提交
    PARTIAL = 2,      // 部分成交
    FILLED = 3,       // 完全成交
    CANCELLED = 4,    // 已撤销
    REJECTED = 5      // 被拒绝
};

// 订单方向
enum class OrderDirection {
    BUY = 0,
    SELL = 1
};

// 订单类型
enum class OrderType {
    MARKET = 0,    // 市价单
    LIMIT = 1,     // 限价单
    STOP = 2       // 止损单
};

// 交易订单
struct TradeOrder {
    std::string order_id;
    std::string symbol;
    OrderDirection direction;
    OrderType type;
    double price;
    int volume;
    OrderStatus status;
    int filled_volume;
    double avg_filled_price;
    std::string submit_time;
    std::string update_time;
    std::string message;
    
    TradeOrder() 
        : direction(OrderDirection::BUY),
          type(OrderType::LIMIT),
          price(0.0),
          volume(0),
          status(OrderStatus::PENDING),
          filled_volume(0),
          avg_filled_price(0.0) {}
};

// 账户信息
struct AccountInfo {
    std::string account_id;
    double total_assets;      // 总资产
    double available_cash;    // 可用资金
    double frozen_cash;       // 冻结资金
    double market_value;      // 持仓市值
    double profit_loss;       // 盈亏
    std::string update_time;
    
    AccountInfo()
        : total_assets(0.0),
          available_cash(0.0),
          frozen_cash(0.0),
          market_value(0.0),
          profit_loss(0.0) {}
};

// 持仓信息
struct PositionInfo {
    std::string symbol;
    int total_volume;         // 总持仓
    int available_volume;     // 可用持仓
    int frozen_volume;        // 冻结持仓
    double avg_price;         // 持仓均价
    double current_price;     // 当前价格
    double market_value;      // 市值
    double profit_loss;       // 盈亏
    double profit_loss_ratio; // 盈亏比例
    
    PositionInfo()
        : total_volume(0),
          available_volume(0),
          frozen_volume(0),
          avg_price(0.0),
          current_price(0.0),
          market_value(0.0),
          profit_loss(0.0),
          profit_loss_ratio(0.0) {}
};

// 成交回报
struct TradeReport {
    std::string trade_id;
    std::string order_id;
    std::string symbol;
    OrderDirection direction;
    double price;
    int volume;
    std::string trade_time;
    double commission;
    
    TradeReport()
        : direction(OrderDirection::BUY),
          price(0.0),
          volume(0),
          commission(0.0) {}
};

/**
 * @brief 交易接口抽象基类
 * 
 * 支持对接不同的交易系统（QMT、XTP、模拟盘等）
 */
class ITradingInterface {
public:
    virtual ~ITradingInterface() = default;
    
    // ==================== 连接管理 ====================
    
    /**
     * @brief 连接到交易系统
     */
    virtual bool connect(const std::string& config) = 0;
    
    /**
     * @brief 断开连接
     */
    virtual void disconnect() = 0;
    
    /**
     * @brief 检查是否已连接
     */
    virtual bool is_connected() const = 0;
    
    /**
     * @brief 登录
     */
    virtual bool login(const std::string& username, const std::string& password) = 0;
    
    // ==================== 订单操作 ====================
    
    /**
     * @brief 提交订单
     */
    virtual std::string submit_order(const TradeOrder& order) = 0;
    
    /**
     * @brief 撤销订单
     */
    virtual bool cancel_order(const std::string& order_id) = 0;
    
    /**
     * @brief 查询订单
     */
    virtual TradeOrder query_order(const std::string& order_id) = 0;
    
    /**
     * @brief 查询所有订单
     */
    virtual std::vector<TradeOrder> query_orders(const std::string& symbol = "") = 0;
    
    // ==================== 账户查询 ====================
    
    /**
     * @brief 查询账户信息
     */
    virtual AccountInfo query_account() = 0;
    
    /**
     * @brief 查询持仓
     */
    virtual std::vector<PositionInfo> query_positions() = 0;
    
    /**
     * @brief 查询单个持仓
     */
    virtual PositionInfo query_position(const std::string& symbol) = 0;
    
    /**
     * @brief 查询成交记录
     */
    virtual std::vector<TradeReport> query_trades() = 0;
    
    // ==================== 回调设置 ====================
    
    /**
     * @brief 设置订单状态回调
     */
    virtual void set_order_callback(std::function<void(const TradeOrder&)> callback) = 0;
    
    /**
     * @brief 设置成交回调
     */
    virtual void set_trade_callback(std::function<void(const TradeReport&)> callback) = 0;
    
    /**
     * @brief 设置错误回调
     */
    virtual void set_error_callback(std::function<void(const std::string&)> callback) = 0;
};

/**
 * @brief 模拟盘交易接口
 */
class SimulatedTrading : public ITradingInterface {
public:
    SimulatedTrading();
    virtual ~SimulatedTrading() = default;
    
    // 连接管理
    bool connect(const std::string& config) override;
    void disconnect() override;
    bool is_connected() const override;
    bool login(const std::string& username, const std::string& password) override;
    
    // 订单操作
    std::string submit_order(const TradeOrder& order) override;
    bool cancel_order(const std::string& order_id) override;
    TradeOrder query_order(const std::string& order_id) override;
    std::vector<TradeOrder> query_orders(const std::string& symbol = "") override;
    
    // 账户查询
    AccountInfo query_account() override;
    std::vector<PositionInfo> query_positions() override;
    PositionInfo query_position(const std::string& symbol) override;
    std::vector<TradeReport> query_trades() override;
    
    // 回调设置
    void set_order_callback(std::function<void(const TradeOrder&)> callback) override;
    void set_trade_callback(std::function<void(const TradeReport&)> callback) override;
    void set_error_callback(std::function<void(const std::string&)> callback) override;
    
    // 模拟盘特有接口
    void set_initial_cash(double cash);
    void update_market_price(const std::string& symbol, double price);
    void process_orders();  // 处理挂单
    
private:
    bool connected_;
    bool logged_in_;
    int next_order_id_;
    int next_trade_id_;
    
    AccountInfo account_;
    std::map<std::string, PositionInfo> positions_;
    std::map<std::string, TradeOrder> orders_;
    std::vector<TradeReport> trades_;
    std::map<std::string, double> market_prices_;
    
    std::function<void(const TradeOrder&)> order_callback_;
    std::function<void(const TradeReport&)> trade_callback_;
    std::function<void(const std::string&)> error_callback_;
    
    void execute_order(TradeOrder& order);
    void update_position(const TradeReport& trade);
    void update_account();
    std::string generate_order_id();
    std::string generate_trade_id();
};

} // namespace trading
} // namespace apexquant

