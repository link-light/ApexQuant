#pragma once

#include "data_structures.h"
#include <vector>
#include <map>
#include <memory>
#include <functional>

namespace apexquant {

/**
 * @brief 回测配置
 */
struct BacktestConfig {
    double initial_capital = 1000000.0;     // 初始资金
    double commission_rate = 0.0003;        // 手续费率
    double min_commission = 5.0;            // 最低手续费
    double slippage_rate = 0.001;           // 滑点率
    bool enable_market_impact = false;      // 是否启用冲击成本
    double market_impact_coef = 0.1;        // 冲击成本系数
    
    BacktestConfig() = default;
};

/**
 * @brief 交易记录
 */
struct Trade {
    std::string symbol;
    int64_t timestamp;
    OrderSide side;
    int64_t quantity;
    double price;
    double commission;
    double slippage;
    std::string strategy_id;
    
    Trade() : timestamp(0), side(OrderSide::BUY), quantity(0), 
             price(0.0), commission(0.0), slippage(0.0) {}
};

/**
 * @brief 回测结果
 */
struct BacktestResult {
    double total_return = 0.0;              // 总收益率
    double annual_return = 0.0;             // 年化收益率
    double sharpe_ratio = 0.0;              // 夏普比率
    double max_drawdown = 0.0;              // 最大回撤
    double win_rate = 0.0;                  // 胜率
    int total_trades = 0;                   // 总交易次数
    int winning_trades = 0;                 // 盈利交易次数
    int losing_trades = 0;                  // 亏损交易次数
    double total_commission = 0.0;          // 总手续费
    double total_slippage = 0.0;            // 总滑点成本
    
    std::vector<double> equity_curve;       // 权益曲线
    std::vector<double> daily_returns;      // 日收益率
    std::vector<Trade> trades;              // 交易记录
};

/**
 * @brief 回测引擎
 */
class BacktestEngine {
public:
    BacktestEngine(const BacktestConfig& config = BacktestConfig());
    ~BacktestEngine() = default;
    
    // 设置数据
    void set_data(const std::vector<Bar>& bars);
    
    // 运行回测
    BacktestResult run();
    
    // 策略接口（供 Python 回调）
    using OnBarCallback = std::function<void(const Bar&)>;
    void set_on_bar_callback(OnBarCallback callback);
    
    // 交易接口
    void buy(const std::string& symbol, int64_t quantity, double limit_price = 0.0);
    void sell(const std::string& symbol, int64_t quantity, double limit_price = 0.0);
    void close_position(const std::string& symbol);
    
    // 查询接口
    double get_cash() const { return cash_; }
    double get_total_value() const;
    Position get_position(const std::string& symbol) const;
    bool has_position(const std::string& symbol) const;
    
private:
    void process_bar(const Bar& bar);
    void execute_order(const Order& order, const Bar& bar);
    double calculate_commission(double value) const;
    double calculate_slippage(double price, int64_t quantity, OrderSide side) const;
    void update_positions(const Bar& bar);
    void record_equity();
    
    BacktestConfig config_;
    std::vector<Bar> data_;
    
    double cash_;
    double initial_cash_;
    std::map<std::string, Position> positions_;
    std::vector<Order> pending_orders_;
    std::vector<Trade> trades_;
    std::vector<double> equity_curve_;
    std::vector<int64_t> timestamps_;
    
    OnBarCallback on_bar_callback_;
    Bar current_bar_;
};

} // namespace apexquant

