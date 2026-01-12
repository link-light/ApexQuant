#pragma once

#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>

namespace apexquant {
namespace indicators {

/**
 * @brief 简单移动平均 (SMA)
 */
std::vector<double> sma(const std::vector<double>& data, int period);

/**
 * @brief 指数移动平均 (EMA)
 */
std::vector<double> ema(const std::vector<double>& data, int period);

/**
 * @brief MACD 指标
 * @return {MACD, Signal, Histogram}
 */
struct MACDResult {
    std::vector<double> macd;
    std::vector<double> signal;
    std::vector<double> histogram;
};

MACDResult macd(const std::vector<double>& data, 
                int fast_period = 12, 
                int slow_period = 26, 
                int signal_period = 9);

/**
 * @brief 相对强弱指标 (RSI)
 */
std::vector<double> rsi(const std::vector<double>& data, int period = 14);

/**
 * @brief 布林带 (Bollinger Bands)
 */
struct BollingerBandsResult {
    std::vector<double> upper;
    std::vector<double> middle;
    std::vector<double> lower;
};

BollingerBandsResult bollinger_bands(const std::vector<double>& data, 
                                     int period = 20, 
                                     double num_std = 2.0);

/**
 * @brief KDJ 指标
 */
struct KDJResult {
    std::vector<double> k;
    std::vector<double> d;
    std::vector<double> j;
};

KDJResult kdj(const std::vector<double>& high,
              const std::vector<double>& low,
              const std::vector<double>& close,
              int period = 9,
              int k_smooth = 3,
              int d_smooth = 3);

/**
 * @brief ATR (Average True Range) 平均真实波动范围
 */
std::vector<double> atr(const std::vector<double>& high,
                       const std::vector<double>& low,
                       const std::vector<double>& close,
                       int period = 14);

/**
 * @brief OBV (On Balance Volume) 能量潮
 */
std::vector<double> obv(const std::vector<double>& close,
                       const std::vector<double>& volume);

/**
 * @brief 动量指标 (Momentum)
 */
std::vector<double> momentum(const std::vector<double>& data, int period = 10);

/**
 * @brief 变动率 (ROC - Rate of Change)
 */
std::vector<double> roc(const std::vector<double>& data, int period = 10);

/**
 * @brief 威廉指标 (Williams %R)
 */
std::vector<double> williams_r(const std::vector<double>& high,
                              const std::vector<double>& low,
                              const std::vector<double>& close,
                              int period = 14);

} // namespace indicators
} // namespace apexquant

