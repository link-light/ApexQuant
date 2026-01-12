#include "indicators.h"
#include <limits>

namespace apexquant {
namespace indicators {

// 简单移动平均 (SMA)
std::vector<double> sma(const std::vector<double>& data, int period) {
    if (data.empty() || period <= 0 || period > static_cast<int>(data.size())) {
        return std::vector<double>(data.size(), std::numeric_limits<double>::quiet_NaN());
    }
    
    std::vector<double> result(data.size(), std::numeric_limits<double>::quiet_NaN());
    
    for (size_t i = period - 1; i < data.size(); ++i) {
        double sum = 0.0;
        for (int j = 0; j < period; ++j) {
            sum += data[i - j];
        }
        result[i] = sum / period;
    }
    
    return result;
}

// 指数移动平均 (EMA)
std::vector<double> ema(const std::vector<double>& data, int period) {
    if (data.empty() || period <= 0) {
        return std::vector<double>(data.size(), std::numeric_limits<double>::quiet_NaN());
    }
    
    std::vector<double> result(data.size(), std::numeric_limits<double>::quiet_NaN());
    
    double multiplier = 2.0 / (period + 1);
    
    // 初始值使用 SMA
    double sum = 0.0;
    for (int i = 0; i < period && i < static_cast<int>(data.size()); ++i) {
        sum += data[i];
    }
    result[period - 1] = sum / period;
    
    // 计算 EMA
    for (size_t i = period; i < data.size(); ++i) {
        result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1];
    }
    
    return result;
}

// MACD
MACDResult macd(const std::vector<double>& data, 
                int fast_period, int slow_period, int signal_period) {
    MACDResult result;
    
    if (data.empty()) {
        return result;
    }
    
    // 计算快慢 EMA
    auto ema_fast = ema(data, fast_period);
    auto ema_slow = ema(data, slow_period);
    
    // MACD 线 = 快线 - 慢线
    result.macd.resize(data.size(), std::numeric_limits<double>::quiet_NaN());
    for (size_t i = 0; i < data.size(); ++i) {
        if (!std::isnan(ema_fast[i]) && !std::isnan(ema_slow[i])) {
            result.macd[i] = ema_fast[i] - ema_slow[i];
        }
    }
    
    // Signal 线 = MACD 的 EMA
    result.signal = ema(result.macd, signal_period);
    
    // Histogram = MACD - Signal
    result.histogram.resize(data.size(), std::numeric_limits<double>::quiet_NaN());
    for (size_t i = 0; i < data.size(); ++i) {
        if (!std::isnan(result.macd[i]) && !std::isnan(result.signal[i])) {
            result.histogram[i] = result.macd[i] - result.signal[i];
        }
    }
    
    return result;
}

// RSI
std::vector<double> rsi(const std::vector<double>& data, int period) {
    if (data.size() < 2 || period <= 0) {
        return std::vector<double>(data.size(), std::numeric_limits<double>::quiet_NaN());
    }
    
    std::vector<double> result(data.size(), std::numeric_limits<double>::quiet_NaN());
    
    // 计算价格变化
    std::vector<double> gains, losses;
    for (size_t i = 1; i < data.size(); ++i) {
        double change = data[i] - data[i - 1];
        gains.push_back(change > 0 ? change : 0.0);
        losses.push_back(change < 0 ? -change : 0.0);
    }
    
    if (gains.size() < static_cast<size_t>(period)) {
        return result;
    }
    
    // 初始平均
    double avg_gain = 0.0, avg_loss = 0.0;
    for (int i = 0; i < period; ++i) {
        avg_gain += gains[i];
        avg_loss += losses[i];
    }
    avg_gain /= period;
    avg_loss /= period;
    
    // 计算 RSI
    for (size_t i = period; i < data.size(); ++i) {
        if (avg_loss == 0.0) {
            result[i] = 100.0;
        } else {
            double rs = avg_gain / avg_loss;
            result[i] = 100.0 - (100.0 / (1.0 + rs));
        }
        
        // 更新平均
        if (i < data.size() - 1) {
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period;
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period;
        }
    }
    
    return result;
}

// 布林带
BollingerBandsResult bollinger_bands(const std::vector<double>& data, 
                                     int period, double num_std) {
    BollingerBandsResult result;
    
    if (data.empty() || period <= 0) {
        return result;
    }
    
    result.middle = sma(data, period);
    result.upper.resize(data.size(), std::numeric_limits<double>::quiet_NaN());
    result.lower.resize(data.size(), std::numeric_limits<double>::quiet_NaN());
    
    for (size_t i = period - 1; i < data.size(); ++i) {
        // 计算标准差
        double sum_sq = 0.0;
        for (int j = 0; j < period; ++j) {
            double diff = data[i - j] - result.middle[i];
            sum_sq += diff * diff;
        }
        double std_dev = std::sqrt(sum_sq / period);
        
        result.upper[i] = result.middle[i] + num_std * std_dev;
        result.lower[i] = result.middle[i] - num_std * std_dev;
    }
    
    return result;
}

// KDJ
KDJResult kdj(const std::vector<double>& high,
              const std::vector<double>& low,
              const std::vector<double>& close,
              int period, int k_smooth, int d_smooth) {
    KDJResult result;
    
    if (high.size() != low.size() || high.size() != close.size() || 
        high.empty() || period <= 0) {
        return result;
    }
    
    size_t n = high.size();
    std::vector<double> rsv(n, std::numeric_limits<double>::quiet_NaN());
    
    // 计算 RSV
    for (size_t i = period - 1; i < n; ++i) {
        double highest = high[i];
        double lowest = low[i];
        
        for (int j = 0; j < period; ++j) {
            highest = std::max(highest, high[i - j]);
            lowest = std::min(lowest, low[i - j]);
        }
        
        if (highest != lowest) {
            rsv[i] = 100.0 * (close[i] - lowest) / (highest - lowest);
        } else {
            rsv[i] = 50.0;
        }
    }
    
    // K 值 (RSV 的 EMA)
    result.k = ema(rsv, k_smooth);
    
    // D 值 (K 的 EMA)
    result.d = ema(result.k, d_smooth);
    
    // J 值 = 3K - 2D
    result.j.resize(n, std::numeric_limits<double>::quiet_NaN());
    for (size_t i = 0; i < n; ++i) {
        if (!std::isnan(result.k[i]) && !std::isnan(result.d[i])) {
            result.j[i] = 3 * result.k[i] - 2 * result.d[i];
        }
    }
    
    return result;
}

// ATR
std::vector<double> atr(const std::vector<double>& high,
                       const std::vector<double>& low,
                       const std::vector<double>& close,
                       int period) {
    if (high.size() != low.size() || high.size() != close.size() || 
        high.size() < 2 || period <= 0) {
        return std::vector<double>(high.size(), std::numeric_limits<double>::quiet_NaN());
    }
    
    // 计算真实波动范围 (True Range)
    std::vector<double> tr(high.size(), std::numeric_limits<double>::quiet_NaN());
    
    for (size_t i = 1; i < high.size(); ++i) {
        double h_l = high[i] - low[i];
        double h_pc = std::abs(high[i] - close[i - 1]);
        double l_pc = std::abs(low[i] - close[i - 1]);
        
        tr[i] = std::max({h_l, h_pc, l_pc});
    }
    
    // ATR = TR 的 EMA
    return ema(tr, period);
}

// OBV
std::vector<double> obv(const std::vector<double>& close,
                       const std::vector<double>& volume) {
    if (close.size() != volume.size() || close.empty()) {
        return std::vector<double>();
    }
    
    std::vector<double> result(close.size(), 0.0);
    result[0] = volume[0];
    
    for (size_t i = 1; i < close.size(); ++i) {
        if (close[i] > close[i - 1]) {
            result[i] = result[i - 1] + volume[i];
        } else if (close[i] < close[i - 1]) {
            result[i] = result[i - 1] - volume[i];
        } else {
            result[i] = result[i - 1];
        }
    }
    
    return result;
}

// 动量
std::vector<double> momentum(const std::vector<double>& data, int period) {
    if (data.empty() || period <= 0 || period >= static_cast<int>(data.size())) {
        return std::vector<double>(data.size(), std::numeric_limits<double>::quiet_NaN());
    }
    
    std::vector<double> result(data.size(), std::numeric_limits<double>::quiet_NaN());
    
    for (size_t i = period; i < data.size(); ++i) {
        result[i] = data[i] - data[i - period];
    }
    
    return result;
}

// ROC
std::vector<double> roc(const std::vector<double>& data, int period) {
    if (data.empty() || period <= 0 || period >= static_cast<int>(data.size())) {
        return std::vector<double>(data.size(), std::numeric_limits<double>::quiet_NaN());
    }
    
    std::vector<double> result(data.size(), std::numeric_limits<double>::quiet_NaN());
    
    for (size_t i = period; i < data.size(); ++i) {
        if (data[i - period] != 0.0) {
            result[i] = 100.0 * (data[i] - data[i - period]) / data[i - period];
        }
    }
    
    return result;
}

// Williams %R
std::vector<double> williams_r(const std::vector<double>& high,
                              const std::vector<double>& low,
                              const std::vector<double>& close,
                              int period) {
    if (high.size() != low.size() || high.size() != close.size() || 
        high.empty() || period <= 0) {
        return std::vector<double>(high.size(), std::numeric_limits<double>::quiet_NaN());
    }
    
    std::vector<double> result(high.size(), std::numeric_limits<double>::quiet_NaN());
    
    for (size_t i = period - 1; i < high.size(); ++i) {
        double highest = high[i];
        double lowest = low[i];
        
        for (int j = 0; j < period; ++j) {
            highest = std::max(highest, high[i - j]);
            lowest = std::min(lowest, low[i - j]);
        }
        
        if (highest != lowest) {
            result[i] = -100.0 * (highest - close[i]) / (highest - lowest);
        } else {
            result[i] = -50.0;
        }
    }
    
    return result;
}

} // namespace indicators
} // namespace apexquant

