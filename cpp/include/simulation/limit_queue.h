/**
 * @file limit_queue.h
 * @brief 涨跌停订单排队机制
 * 
 * 模拟A股涨跌停时的订单排队等待成交
 */

#ifndef APEXQUANT_SIMULATION_LIMIT_QUEUE_H
#define APEXQUANT_SIMULATION_LIMIT_QUEUE_H

#include "simulation_types.h"
#include "data_structures.h"
#include <vector>
#include <unordered_map>
#include <mutex>
#include <string>

namespace apexquant {
namespace simulation {

/**
 * @brief 涨跌停状态
 */
enum class LimitStatus {
    NORMAL = 0,      // 正常
    LIMIT_UP = 1,    // 涨停
    LIMIT_DOWN = 2   // 跌停
};

/**
 * @brief 涨跌停排队管理器
 * 
 * 功能：
 * - 涨停时买单排队等待
 * - 跌停时卖单排队等待
 * - 价格打开时按时间优先成交
 * - 部分成交模拟
 */
class LimitQueue {
public:
    LimitQueue();
    ~LimitQueue() = default;
    
    /**
     * @brief 将订单加入涨停排队
     * @param order 订单
     */
    void add_to_limit_up_queue(const SimulatedOrder& order);
    
    /**
     * @brief 将订单加入跌停排队
     * @param order 订单
     */
    void add_to_limit_down_queue(const SimulatedOrder& order);
    
    /**
     * @brief 尝试成交涨停排队订单
     * @param symbol 股票代码
     * @param tick 当前行情
     * @return 成交的订单列表
     */
    std::vector<SimulatedOrder> try_fill_limit_up_orders(
        const std::string& symbol,
        const Tick& tick
    );
    
    /**
     * @brief 尝试成交跌停排队订单
     * @param symbol 股票代码
     * @param tick 当前行情
     * @return 成交的订单列表
     */
    std::vector<SimulatedOrder> try_fill_limit_down_orders(
        const std::string& symbol,
        const Tick& tick
    );
    
    /**
     * @brief 检查股票是否涨停
     * @param symbol 股票代码
     * @param current_price 当前价格
     * @param last_close 昨收价
     * @return 涨跌停状态
     */
    LimitStatus check_limit_status(
        const std::string& symbol,
        double current_price,
        double last_close
    );
    
    /**
     * @brief 从排队中移除订单（撤单）
     * @param order_id 订单ID
     * @return 是否成功
     */
    bool remove_from_queue(const std::string& order_id);
    
    /**
     * @brief 获取涨停排队订单数量
     * @param symbol 股票代码
     * @return 排队订单数
     */
    size_t get_limit_up_queue_size(const std::string& symbol) const;
    
    /**
     * @brief 获取跌停排队订单数量
     * @param symbol 股票代码
     * @return 排队订单数
     */
    size_t get_limit_down_queue_size(const std::string& symbol) const;
    
    /**
     * @brief 清空所有排队订单
     */
    void clear_all_queues();

private:
    // 涨停排队：symbol -> orders (按时间排序)
    std::unordered_map<std::string, std::vector<SimulatedOrder>> limit_up_queues_;
    
    // 跌停排队：symbol -> orders (按时间排序)
    std::unordered_map<std::string, std::vector<SimulatedOrder>> limit_down_queues_;
    
    // 线程安全
    mutable std::mutex mutex_;
    
    /**
     * @brief 获取涨跌停幅度
     */
    double get_limit_pct(const std::string& symbol) const;
    
    /**
     * @brief 计算涨停价
     */
    double calculate_limit_up_price(const std::string& symbol, double last_close) const;
    
    /**
     * @brief 计算跌停价
     */
    double calculate_limit_down_price(const std::string& symbol, double last_close) const;
    
    /**
     * @brief 价格是否触及涨停
     */
    bool is_at_limit_up(const std::string& symbol, double price, double last_close) const;
    
    /**
     * @brief 价格是否触及跌停
     */
    bool is_at_limit_down(const std::string& symbol, double price, double last_close) const;
};

} // namespace simulation
} // namespace apexquant

#endif // APEXQUANT_SIMULATION_LIMIT_QUEUE_H
















