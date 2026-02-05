/**
 * @file simulated_exchange.h
 * @brief ApexQuant模拟交易所
 * 
 * 整合账户管理和订单撮合，提供完整的模拟交易功能
 */

#ifndef APEXQUANT_SIMULATION_EXCHANGE_H
#define APEXQUANT_SIMULATION_EXCHANGE_H

#include "simulation_account.h"
#include "order_matcher.h"
#include "data_structures.h"
#include <unordered_map>
#include <vector>
#include <mutex>
#include <string>

namespace apexquant {
namespace simulation {

/**
 * @brief 模拟交易所
 * 
 * 整合功能：
 * - 订单提交（资金/持仓冻结）
 * - 行情驱动撮合（on_tick）
 * - 订单撤销
 * - 持仓/资金查询
 * - 成交历史
 */
class SimulatedExchange {
public:
    /**
     * @brief 构造函数
     * @param account_id 账户ID
     * @param initial_capital 初始资金
     */
    SimulatedExchange(const std::string& account_id, double initial_capital);
    
    /**
     * @brief 析构函数
     */
    ~SimulatedExchange() = default;
    
    // ========================================================================
    // 订单管理
    // ========================================================================
    
    /**
     * @brief 提交订单
     * @param order 订单信息（order_id会被重新生成）
     * @return 订单ID
     */
    std::string submit_order(SimulatedOrder order);
    
    /**
     * @brief 行情更新触发撮合
     * @param tick 最新行情
     */
    void on_tick(const Tick& tick);
    
    /**
     * @brief 撤销订单
     * @param order_id 订单ID
     * @return 是否成功
     */
    bool cancel_order(const std::string& order_id);
    
    // ========================================================================
    // 查询方法
    // ========================================================================
    
    /**
     * @brief 获取订单
     */
    SimulatedOrder get_order(const std::string& order_id) const;
    
    /**
     * @brief 获取所有待成交订单
     */
    std::vector<SimulatedOrder> get_pending_orders() const;
    
    /**
     * @brief 获取指定股票的待成交订单
     */
    std::vector<SimulatedOrder> get_pending_orders(const std::string& symbol) const;
    
    /**
     * @brief 获取成交历史
     */
    std::vector<TradeRecord> get_trade_history() const;
    
    /**
     * @brief 获取持仓
     */
    Position get_position(const std::string& symbol) const;
    
    /**
     * @brief 获取所有持仓
     */
    std::vector<Position> get_all_positions() const;
    
    /**
     * @brief 获取总资产
     */
    double get_total_assets() const;
    
    /**
     * @brief 获取可用现金
     */
    double get_available_cash() const;
    
    /**
     * @brief 获取冻结资金
     */
    double get_frozen_cash() const;
    
    // ========================================================================
    // 日常维护
    // ========================================================================
    
    /**
     * @brief 每日开盘调用，解锁T+1持仓
     * @param current_date 当前日期（格式：20250203）
     */
    void update_daily(int64_t current_date);
    
    /**
     * @brief 获取账户ID
     */
    std::string get_account_id() const;

private:
    SimulationAccount account_;      // 账户管理
    OrderMatcher matcher_;           // 撮合引擎
    
    std::unordered_map<std::string, SimulatedOrder> orders_;  // 所有订单
    std::vector<TradeRecord> trade_history_;                   // 成交历史
    
    int64_t current_time_;           // 当前时间
    int64_t order_counter_;          // 订单计数器
    
    mutable std::mutex mutex_;       // 线程安全
    
    /**
     * @brief 生成唯一订单ID
     */
    std::string generate_order_id(const std::string& symbol);
    
    /**
     * @brief 处理订单成交
     */
    void process_fill(
        SimulatedOrder& order,
        const MatchResult& match_result,
        int64_t current_date
    );
    
    /**
     * @brief 处理订单拒绝
     */
    void process_reject(
        SimulatedOrder& order,
        const std::string& reason
    );
    
    /**
     * @brief 计算手续费
     */
    double calculate_commission(
        OrderSide side,
        double filled_price,
        int64_t filled_volume
    );
};

} // namespace simulation
} // namespace apexquant

#endif // APEXQUANT_SIMULATION_EXCHANGE_H
