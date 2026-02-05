/**
 * @file order_matcher.h
 * @brief ApexQuant订单撮合引擎
 * 
 * 实现市价单/限价单撮合、涨跌停检查、滑点计算、流动性检查
 */

#ifndef APEXQUANT_SIMULATION_ORDER_MATCHER_H
#define APEXQUANT_SIMULATION_ORDER_MATCHER_H

#include "simulation_types.h"
#include "data_structures.h"  // 引入主项目的Tick定义
#include <random>
#include <string>

namespace apexquant {
namespace simulation {

/**
 * @brief 订单撮合引擎
 * 
 * 功能：
 * - 市价单/限价单撮合逻辑
 * - 涨跌停价格检查（10%/5%/20%）
 * - 滑点计算（随机+大单惩罚）
 * - 流动性检查
 * - 手续费和印花税计算
 */
class OrderMatcher {
public:
    /**
     * @brief 构造函数
     * @param default_slippage_rate 默认滑点率（万一）
     * @param default_commission_rate 默认手续费率（万2.5）
     * @param stamp_tax_rate 印花税率（千一，仅卖出）
     */
    OrderMatcher(
        double default_slippage_rate = 0.0001,
        double default_commission_rate = 0.00025,
        double stamp_tax_rate = 0.001
    );
    
    /**
     * @brief 尝试撮合订单
     * @param order 订单信息
     * @param current_tick 当前行情
     * @param check_price_limit 是否检查涨跌停（默认true）
     * @return 撮合结果
     */
    MatchResult try_match_order(
        const SimulatedOrder& order,
        const Tick& current_tick,
        bool check_price_limit = true
    );
    
    /**
     * @brief 检查价格是否在涨跌停范围内
     * @param symbol 股票代码
     * @param price 价格
     * @param last_close 昨收价
     * @return true表示价格合法
     */
    bool check_limit_price(
        const std::string& symbol, 
        double price, 
        double last_close
    );
    
    /**
     * @brief 计算滑点
     * @param side 买卖方向
     * @param base_price 基准价格
     * @param volume 数量
     * @param slippage_rate 滑点率
     * @return 实际成交价格
     */
    double calculate_slippage(
        OrderSide side,
        double base_price,
        int64_t volume,
        double slippage_rate
    );
    
    /**
     * @brief 检查流动性
     * @param volume 订单数量
     * @param tick 行情数据
     * @param side 买卖方向
     * @return true表示流动性充足
     */
    bool check_liquidity(
        int64_t volume, 
        const Tick& tick, 
        OrderSide side
    );
    
    /**
     * @brief 验证订单数量是否合法
     * @param volume 订单数量
     * @param side 买卖方向
     * @param available_volume 可卖数量（仅卖出时使用）
     * @return {是否合法, 错误信息}
     */
    std::pair<bool, std::string> validate_order_volume(
        int64_t volume,
        OrderSide side,
        int64_t available_volume = 0
    );
    
    /**
     * @brief 计算完整的交易费用
     * @param side 买卖方向
     * @param symbol 股票代码
     * @param price 价格
     * @param volume 数量
     * @param commission_rate 佣金率
     * @return 总费用（佣金+印花税+过户费）
     */
    double calculate_total_commission(
        OrderSide side,
        const std::string& symbol,
        double price,
        int64_t volume,
        double commission_rate
    );

private:
    double default_slippage_rate_;     // 默认滑点率
    double default_commission_rate_;   // 默认手续费率
    double stamp_tax_rate_;            // 印花税率
    
    std::mt19937 rng_;                 // 随机数生成器
    std::uniform_real_distribution<double> dist_;  // 均匀分布[-1, 1]
    
    /**
     * @brief 获取涨跌停幅度
     * @param symbol 股票代码
     * @return 涨跌停幅度（例如0.1表示10%）
     */
    double get_limit_pct(const std::string& symbol);
    
    /**
     * @brief 四舍五入到分
     */
    double round_to_cent(double value);
};

} // namespace simulation
} // namespace apexquant

#endif // APEXQUANT_SIMULATION_ORDER_MATCHER_H
