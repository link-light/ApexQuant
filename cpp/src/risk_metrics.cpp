#include "risk_metrics.h"
#include <limits>

namespace apexquant {
namespace risk {

double value_at_risk(const std::vector<double>& returns, double confidence) {
    if (returns.empty()) return 0.0;
    
    std::vector<double> sorted_returns = returns;
    std::sort(sorted_returns.begin(), sorted_returns.end());
    
    size_t index = static_cast<size_t>((1.0 - confidence) * sorted_returns.size());
    if (index >= sorted_returns.size()) {
        index = sorted_returns.size() - 1;
    }
    
    return -sorted_returns[index];  // 返回正数表示损失
}

double conditional_var(const std::vector<double>& returns, double confidence) {
    if (returns.empty()) return 0.0;
    
    std::vector<double> sorted_returns = returns;
    std::sort(sorted_returns.begin(), sorted_returns.end());
    
    size_t cutoff = static_cast<size_t>((1.0 - confidence) * sorted_returns.size());
    if (cutoff == 0) cutoff = 1;
    
    double sum = 0.0;
    for (size_t i = 0; i < cutoff; ++i) {
        sum += sorted_returns[i];
    }
    
    return -(sum / cutoff);  // 返回正数表示损失
}

double calmar_ratio(double annual_return, double max_drawdown) {
    if (max_drawdown <= 0.0) return 0.0;
    return annual_return / max_drawdown;
}

double sortino_ratio(const std::vector<double>& returns, 
                    double risk_free_rate,
                    int periods_per_year) {
    if (returns.empty()) return 0.0;
    
    double mean_return = std::accumulate(returns.begin(), returns.end(), 0.0) / returns.size();
    double annual_mean = mean_return * periods_per_year;
    
    double downside_dev = downside_std(returns, 0.0);
    double annual_downside = downside_dev * std::sqrt(static_cast<double>(periods_per_year));
    
    if (annual_downside == 0.0) return 0.0;
    
    return (annual_mean - risk_free_rate) / annual_downside;
}

double omega_ratio(const std::vector<double>& returns, double threshold) {
    if (returns.empty()) return 0.0;
    
    double gains = 0.0;
    double losses = 0.0;
    
    for (double ret : returns) {
        if (ret > threshold) {
            gains += (ret - threshold);
        } else {
            losses += (threshold - ret);
        }
    }
    
    if (losses == 0.0) return std::numeric_limits<double>::infinity();
    
    return gains / losses;
}

double max_drawdown(const std::vector<double>& equity_curve) {
    if (equity_curve.empty()) return 0.0;
    
    double peak = equity_curve[0];
    double max_dd = 0.0;
    
    for (double value : equity_curve) {
        if (value > peak) {
            peak = value;
        }
        
        double drawdown = (peak - value) / peak;
        if (drawdown > max_dd) {
            max_dd = drawdown;
        }
    }
    
    return max_dd;
}

std::vector<double> drawdown_series(const std::vector<double>& equity_curve) {
    std::vector<double> drawdowns(equity_curve.size(), 0.0);
    
    if (equity_curve.empty()) return drawdowns;
    
    double peak = equity_curve[0];
    
    for (size_t i = 0; i < equity_curve.size(); ++i) {
        if (equity_curve[i] > peak) {
            peak = equity_curve[i];
        }
        
        drawdowns[i] = (peak - equity_curve[i]) / peak;
    }
    
    return drawdowns;
}

int max_drawdown_duration(const std::vector<double>& equity_curve) {
    if (equity_curve.empty()) return 0;
    
    int max_duration = 0;
    int current_duration = 0;
    double peak = equity_curve[0];
    
    for (size_t i = 0; i < equity_curve.size(); ++i) {
        if (equity_curve[i] >= peak) {
            peak = equity_curve[i];
            
            if (current_duration > max_duration) {
                max_duration = current_duration;
            }
            current_duration = 0;
        } else {
            current_duration++;
        }
    }
    
    if (current_duration > max_duration) {
        max_duration = current_duration;
    }
    
    return max_duration;
}

double information_ratio(const std::vector<double>& returns,
                        const std::vector<double>& benchmark_returns,
                        int periods_per_year) {
    if (returns.size() != benchmark_returns.size() || returns.empty()) {
        return 0.0;
    }
    
    // 计算超额收益
    std::vector<double> excess_returns(returns.size());
    for (size_t i = 0; i < returns.size(); ++i) {
        excess_returns[i] = returns[i] - benchmark_returns[i];
    }
    
    double mean_excess = std::accumulate(excess_returns.begin(), excess_returns.end(), 0.0) / excess_returns.size();
    
    // 计算跟踪误差（超额收益的标准差）
    double variance = 0.0;
    for (double er : excess_returns) {
        variance += (er - mean_excess) * (er - mean_excess);
    }
    double tracking_error = std::sqrt(variance / excess_returns.size());
    
    if (tracking_error == 0.0) return 0.0;
    
    return (mean_excess * periods_per_year) / (tracking_error * std::sqrt(static_cast<double>(periods_per_year)));
}

double downside_std(const std::vector<double>& returns, double threshold) {
    if (returns.empty()) return 0.0;
    
    double sum_sq = 0.0;
    int count = 0;
    
    for (double ret : returns) {
        if (ret < threshold) {
            double diff = ret - threshold;
            sum_sq += diff * diff;
            count++;
        }
    }
    
    if (count == 0) return 0.0;
    
    return std::sqrt(sum_sq / count);
}

double beta(const std::vector<double>& returns,
           const std::vector<double>& market_returns) {
    if (returns.size() != market_returns.size() || returns.empty()) {
        return 1.0;
    }
    
    double mean_returns = std::accumulate(returns.begin(), returns.end(), 0.0) / returns.size();
    double mean_market = std::accumulate(market_returns.begin(), market_returns.end(), 0.0) / market_returns.size();
    
    double covariance = 0.0;
    double market_variance = 0.0;
    
    for (size_t i = 0; i < returns.size(); ++i) {
        covariance += (returns[i] - mean_returns) * (market_returns[i] - mean_market);
        market_variance += (market_returns[i] - mean_market) * (market_returns[i] - mean_market);
    }
    
    if (market_variance == 0.0) return 1.0;
    
    return covariance / market_variance;
}

double alpha(const std::vector<double>& returns,
            const std::vector<double>& market_returns,
            double risk_free_rate,
            int periods_per_year) {
    if (returns.empty()) return 0.0;
    
    double mean_return = std::accumulate(returns.begin(), returns.end(), 0.0) / returns.size();
    double mean_market = std::accumulate(market_returns.begin(), market_returns.end(), 0.0) / market_returns.size();
    
    double beta_val = beta(returns, market_returns);
    
    double annual_return = mean_return * periods_per_year;
    double annual_market = mean_market * periods_per_year;
    
    return annual_return - risk_free_rate - beta_val * (annual_market - risk_free_rate);
}

double win_rate(const std::vector<double>& returns) {
    if (returns.empty()) return 0.0;
    
    int wins = 0;
    for (double ret : returns) {
        if (ret > 0) wins++;
    }
    
    return static_cast<double>(wins) / returns.size();
}

double profit_loss_ratio(const std::vector<double>& returns) {
    if (returns.empty()) return 0.0;
    
    double total_profit = 0.0;
    double total_loss = 0.0;
    int profit_count = 0;
    int loss_count = 0;
    
    for (double ret : returns) {
        if (ret > 0) {
            total_profit += ret;
            profit_count++;
        } else if (ret < 0) {
            total_loss += -ret;
            loss_count++;
        }
    }
    
    if (loss_count == 0 || total_loss == 0.0) {
        return profit_count > 0 ? std::numeric_limits<double>::infinity() : 0.0;
    }
    
    double avg_profit = total_profit / profit_count;
    double avg_loss = total_loss / loss_count;
    
    return avg_profit / avg_loss;
}

double tail_ratio(const std::vector<double>& returns, double percentile) {
    if (returns.empty()) return 0.0;
    
    std::vector<double> sorted_returns = returns;
    std::sort(sorted_returns.begin(), sorted_returns.end());
    
    size_t upper_index = static_cast<size_t>(percentile * sorted_returns.size());
    size_t lower_index = static_cast<size_t>((1.0 - percentile) * sorted_returns.size());
    
    if (upper_index >= sorted_returns.size()) upper_index = sorted_returns.size() - 1;
    if (lower_index >= sorted_returns.size()) lower_index = 0;
    
    double upper_tail = sorted_returns[upper_index];
    double lower_tail = sorted_returns[lower_index];
    
    if (lower_tail >= 0) return std::numeric_limits<double>::infinity();
    
    return std::abs(upper_tail / lower_tail);
}

} // namespace risk
} // namespace apexquant

