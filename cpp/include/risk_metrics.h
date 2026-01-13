#pragma once

#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>

namespace apexquant {
namespace risk {

/**
 * @brief VaR (Value at Risk) - 风险价值
 * @param returns 收益率序列
 * @param confidence 置信水平 (如 0.95 表示 95% VaR)
 * @return VaR 值
 */
double value_at_risk(const std::vector<double>& returns, double confidence = 0.95);

/**
 * @brief CVaR (Conditional VaR) - 条件风险价值/期望损失
 * @param returns 收益率序列
 * @param confidence 置信水平
 * @return CVaR 值
 */
double conditional_var(const std::vector<double>& returns, double confidence = 0.95);

/**
 * @brief Calmar 比率
 * @param annual_return 年化收益率
 * @param max_drawdown 最大回撤
 * @return Calmar 比率
 */
double calmar_ratio(double annual_return, double max_drawdown);

/**
 * @brief Sortino 比率
 * @param returns 收益率序列
 * @param risk_free_rate 无风险利率 (年化)
 * @param periods_per_year 每年周期数 (日线=252)
 * @return Sortino 比率
 */
double sortino_ratio(const std::vector<double>& returns, 
                    double risk_free_rate = 0.0,
                    int periods_per_year = 252);

/**
 * @brief Omega 比率
 * @param returns 收益率序列
 * @param threshold 阈值收益率
 * @return Omega 比率
 */
double omega_ratio(const std::vector<double>& returns, double threshold = 0.0);

/**
 * @brief 最大回撤
 * @param equity_curve 权益曲线
 * @return 最大回撤（正数）
 */
double max_drawdown(const std::vector<double>& equity_curve);

/**
 * @brief 计算回撤序列
 * @param equity_curve 权益曲线
 * @return 回撤序列
 */
std::vector<double> drawdown_series(const std::vector<double>& equity_curve);

/**
 * @brief 最大回撤持续时间（天数）
 * @param equity_curve 权益曲线
 * @return 持续天数
 */
int max_drawdown_duration(const std::vector<double>& equity_curve);

/**
 * @brief 信息比率 (Information Ratio)
 * @param returns 策略收益率
 * @param benchmark_returns 基准收益率
 * @param periods_per_year 每年周期数
 * @return 信息比率
 */
double information_ratio(const std::vector<double>& returns,
                        const std::vector<double>& benchmark_returns,
                        int periods_per_year = 252);

/**
 * @brief 下行标准差
 * @param returns 收益率序列
 * @param threshold 阈值
 * @return 下行标准差
 */
double downside_std(const std::vector<double>& returns, double threshold = 0.0);

/**
 * @brief Beta 系数
 * @param returns 策略收益率
 * @param market_returns 市场收益率
 * @return Beta 值
 */
double beta(const std::vector<double>& returns,
           const std::vector<double>& market_returns);

/**
 * @brief Alpha 系数
 * @param returns 策略收益率
 * @param market_returns 市场收益率
 * @param risk_free_rate 无风险利率
 * @param periods_per_year 每年周期数
 * @return Alpha 值
 */
double alpha(const std::vector<double>& returns,
            const std::vector<double>& market_returns,
            double risk_free_rate = 0.0,
            int periods_per_year = 252);

/**
 * @brief 胜率
 * @param returns 收益率序列
 * @return 胜率 (0-1)
 */
double win_rate(const std::vector<double>& returns);

/**
 * @brief 盈亏比
 * @param returns 收益率序列
 * @return 盈亏比
 */
double profit_loss_ratio(const std::vector<double>& returns);

/**
 * @brief 尾部比率 (Tail Ratio)
 * @param returns 收益率序列
 * @param percentile 分位数 (默认 95%)
 * @return 尾部比率
 */
double tail_ratio(const std::vector<double>& returns, double percentile = 0.95);

} // namespace risk
} // namespace apexquant

