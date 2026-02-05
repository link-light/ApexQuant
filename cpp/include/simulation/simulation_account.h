/**
 * @file simulation_account.h
 * @brief ApexQuant模拟账户管理类
 * 
 * 管理账户资金、持仓、T+1规则等
 */

#ifndef APEXQUANT_SIMULATION_ACCOUNT_H
#define APEXQUANT_SIMULATION_ACCOUNT_H

#include "simulation_types.h"
#include <unordered_map>
#include <vector>
#include <mutex>
#include <string>
#include <cstdint>

namespace apexquant {
namespace simulation {

/**
 * @brief 模拟账户管理类
 * 
 * 功能：
 * - 资金管理（可用、冻结）
 * - 持仓管理（买入、卖出、T+1）
 * - 绩效统计（盈亏计算）
 * - 线程安全（使用互斥锁）
 */
class SimulationAccount {
public:
    /**
     * @brief 构造函数
     * @param account_id 账户ID
     * @param initial_capital 初始资金
     */
    SimulationAccount(const std::string& account_id, double initial_capital);
    
    /**
     * @brief 析构函数
     */
    ~SimulationAccount() = default;
    
    // ========================================================================
    // 资金管理
    // ========================================================================
    
    /**
     * @brief 获取总资产（现金 + 市值）
     */
    double get_total_assets() const;
    
    /**
     * @brief 获取可用现金（可交易）
     */
    double get_available_cash() const;
    
    /**
     * @brief 获取可取资金（可提现，T+1）
     */
    double get_withdrawable_cash() const;
    
    /**
     * @brief 获取冻结资金
     */
    double get_frozen_cash() const;
    
    /**
     * @brief 冻结资金
     * @param amount 冻结金额
     * @return 是否成功
     */
    bool freeze_cash(double amount);
    
    /**
     * @brief 解冻资金
     * @param amount 解冻金额
     */
    void unfreeze_cash(double amount);
    
    // ========================================================================
    // 持仓管理
    // ========================================================================
    
    /**
     * @brief 增加持仓
     * @param symbol 股票代码
     * @param volume 数量
     * @param price 价格
     * @param buy_date 买入日期（格式：20250203）
     * @return 是否成功
     */
    bool add_position(const std::string& symbol, int64_t volume, 
                     double price, int64_t buy_date);
    
    /**
     * @brief 减少持仓
     * @param symbol 股票代码
     * @param volume 数量
     * @param sell_price 卖出价格
     * @param realized_pnl 输出已实现盈亏
     * @return 是否成功
     */
    bool reduce_position(const std::string& symbol, int64_t volume, 
                        double sell_price, double& realized_pnl);
    
    /**
     * @brief 获取单个持仓
     * @param symbol 股票代码
     * @return 持仓信息（不存在则volume=0）
     */
    Position get_position(const std::string& symbol) const;
    
    /**
     * @brief 获取所有持仓
     * @return 持仓列表
     */
    std::vector<Position> get_all_positions() const;
    
    /**
     * @brief 更新持仓价格
     * @param symbol 股票代码
     * @param current_price 当前价格
     */
    void update_position_price(const std::string& symbol, double current_price);
    
    // ========================================================================
    // T+1相关
    // ========================================================================
    
    /**
     * @brief 更新可卖数量（每日开盘调用）
     * @param current_date 当前日期（格式：20250203）
     */
    void update_available_volume(int64_t current_date);
    
    /**
     * @brief 每日结算（更新可取资金）
     * 
     * 功能：
     * - 将今日卖出的资金转为可取资金（T+1）
     * - 更新持仓可卖数量
     */
    void daily_settlement(int64_t current_date);
    
    /**
     * @brief 检查是否可卖（T+1规则）
     * @param symbol 股票代码
     * @param volume 数量
     * @param current_date 当前日期
     * @return 是否可卖
     */
    bool can_sell(const std::string& symbol, int64_t volume, 
                 int64_t current_date) const;
    
    /**
     * @brief 冻结持仓（挂卖单时）
     * @param symbol 股票代码
     * @param volume 数量
     * @return 是否成功
     */
    bool freeze_position(const std::string& symbol, int64_t volume);
    
    /**
     * @brief 解冻持仓（撤单时）
     * @param symbol 股票代码
     * @param volume 数量
     */
    void unfreeze_position(const std::string& symbol, int64_t volume);
    
    // ========================================================================
    // 绩效统计
    // ========================================================================
    
    /**
     * @brief 获取总盈亏
     */
    double get_total_pnl() const;
    
    /**
     * @brief 获取浮动盈亏
     */
    double get_unrealized_pnl() const;
    
    /**
     * @brief 获取已实现盈亏
     */
    double get_realized_pnl() const;
    
    /**
     * @brief 获取账户ID
     */
    std::string get_account_id() const { return account_id_; }
    
    /**
     * @brief 获取初始资金
     */
    double get_initial_capital() const { return initial_capital_; }

private:
    // 账户基本信息
    std::string account_id_;        // 账户ID
    double initial_capital_;        // 初始资金
    double available_cash_;         // 可用现金（可交易）
    double withdrawable_cash_;      // 可取资金（可提现，T+1）
    double frozen_cash_;            // 冻结资金
    double today_sell_amount_;      // 今日卖出金额（明日可取）
    double realized_pnl_;           // 已实现盈亏
    
    // 持仓信息
    std::unordered_map<std::string, Position> positions_;
    
    // 线程安全
    mutable std::mutex mutex_;
    
    // 辅助方法
    
    /**
     * @brief 四舍五入到分（0.01）
     */
    double round_to_cent(double value) const;
};

} // namespace simulation
} // namespace apexquant

#endif // APEXQUANT_SIMULATION_ACCOUNT_H
