/**
 * @file order_matcher.cpp
 * @brief ApexQuant订单撮合引擎实现
 */

#include "simulation/order_matcher.h"
#include <cmath>
#include <algorithm>
#include <chrono>

namespace apexquant {
namespace simulation {

OrderMatcher::OrderMatcher(
    double default_slippage_rate,
    double default_commission_rate,
    double stamp_tax_rate
) : default_slippage_rate_(default_slippage_rate),
    default_commission_rate_(default_commission_rate),
    stamp_tax_rate_(stamp_tax_rate),
    dist_(-1.0, 1.0) {
    
    // 使用当前时间作为随机数种子
    auto seed = std::chrono::high_resolution_clock::now().time_since_epoch().count();
    rng_.seed(static_cast<unsigned int>(seed));
}

MatchResult OrderMatcher::try_match_order(
    const SimulatedOrder& order,
    const Tick& current_tick,
    bool check_price_limit
) {
    // 1. 检查基本有效性
    if (order.volume <= 0) {
        return MatchResult("Order volume must be positive");
    }
    
    // 2. 确定基准价格
    double base_price = 0.0;
    
    if (order.type == OrderType::MARKET) {
        // 市价单：买入按ask价，卖出按bid价
        if (order.side == OrderSide::BUY) {
            base_price = current_tick.ask_price;
        } else {
            base_price = current_tick.bid_price;
        }
    } else {
        // 限价单：需要检查价格是否满足成交条件
        if (order.side == OrderSide::BUY) {
            // 买入限价单：只有当 ask_price <= order.price 时成交
            if (current_tick.ask_price > order.price) {
                return MatchResult("Buy limit price too low");
            }
            base_price = order.price;  // 按限价成交
        } else {
            // 卖出限价单：只有当 bid_price >= order.price 时成交
            if (current_tick.bid_price < order.price) {
                return MatchResult("Sell limit price too high");
            }
            base_price = order.price;  // 按限价成交
        }
    }
    
    // 3. 检查涨跌停（如果启用）
    if (check_price_limit && current_tick.last_close > 0) {
        if (!check_limit_price(order.symbol, base_price, current_tick.last_close)) {
            if (order.side == OrderSide::BUY) {
                return MatchResult("Price at limit up");
            } else {
                return MatchResult("Price at limit down");
            }
        }
    }
    
    // 4. 检查流动性
    if (!check_liquidity(order.volume, current_tick, order.side)) {
        return MatchResult("Insufficient liquidity");
    }
    
    // 5. 计算滑点
    double slippage_rate = order.slippage_rate > 0 ? order.slippage_rate : default_slippage_rate_;
    double filled_price = calculate_slippage(
        order.side,
        base_price,
        order.volume,
        slippage_rate
    );
    
    // 6. 返回成交结果
    return MatchResult(filled_price, order.volume);
}

bool OrderMatcher::check_limit_price(
    const std::string& symbol, 
    double price, 
    double last_close
) {
    if (last_close <= 0) {
        return true;  // 无昨收价，不检查
    }
    
    double limit_pct = get_limit_pct(symbol);
    double limit_up = last_close * (1.0 + limit_pct);
    double limit_down = last_close * (1.0 - limit_pct);
    
    return price >= limit_down && price <= limit_up;
}

double OrderMatcher::calculate_slippage(
    OrderSide side,
    double base_price,
    int64_t volume,
    double slippage_rate
) {
    // 1. 基础滑点：随机 [-slippage_rate, slippage_rate]
    double random_slippage = slippage_rate * dist_(rng_);
    
    // 2. 大单惩罚：超过10000股，滑点率增加50%
    if (volume > 10000) {
        slippage_rate *= 1.5;
        random_slippage = slippage_rate * dist_(rng_);
    }
    
    // 3. 买入正滑点（价格上涨），卖出负滑点（价格下跌）
    double actual_slippage = 0.0;
    if (side == OrderSide::BUY) {
        actual_slippage = std::abs(random_slippage);  // 买入价格上涨
    } else {
        actual_slippage = -std::abs(random_slippage);  // 卖出价格下跌
    }
    
    // 4. 计算实际价格
    double filled_price = base_price * (1.0 + actual_slippage);
    
    return round_to_cent(filled_price);
}

bool OrderMatcher::check_liquidity(
    int64_t volume, 
    const Tick& tick, 
    OrderSide side
) {
    // 简化规则：单笔成交量不超过当前tick成交量的10%
    // 实际场景中这个值可能需要调整
    
    if (tick.volume <= 0) {
        return true;  // 无成交量数据，不检查
    }
    
    int64_t max_volume = tick.volume / 10;
    
    return volume <= max_volume;
}

double OrderMatcher::get_limit_pct(const std::string& symbol) {
    // 根据股票代码判断涨跌停幅度
    
    // ST股票：5%
    if (symbol.find("ST") != std::string::npos || 
        symbol.find("st") != std::string::npos) {
        return 0.05;
    }
    
    // 科创板（688开头）：20%
    if (symbol.length() >= 3 && symbol.substr(0, 3) == "688") {
        return 0.20;
    }
    
    // 创业板（300开头）：20%
    if (symbol.length() >= 3 && symbol.substr(0, 3) == "300") {
        return 0.20;
    }
    
    // 北交所（8或4开头）：30%
    if (symbol.length() >= 1 && (symbol[0] == '8' || symbol[0] == '4')) {
        return 0.30;
    }
    
    // 普通A股：10%
    return 0.10;
}

double OrderMatcher::round_to_cent(double value) {
    return std::round(value * 100.0) / 100.0;
}

} // namespace simulation
} // namespace apexquant
