#pragma once

#include <vector>
#include <numeric>
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace apexquant {
namespace utils {

/**
 * @brief 计算向量的均值
 * @param data 输入数据向量
 * @return 均值
 */
template<typename T>
double calculate_mean(const std::vector<T>& data) {
    if (data.empty()) {
        throw std::invalid_argument("Cannot calculate mean of empty vector");
    }
    
    double sum = std::accumulate(data.begin(), data.end(), 0.0);
    return sum / static_cast<double>(data.size());
}

/**
 * @brief 计算向量的标准差
 * @param data 输入数据向量
 * @param sample 是否使用样本标准差（除以 n-1）
 * @return 标准差
 */
template<typename T>
double calculate_std(const std::vector<T>& data, bool sample = true) {
    if (data.empty()) {
        throw std::invalid_argument("Cannot calculate std of empty vector");
    }
    
    double mean = calculate_mean(data);
    double sq_sum = 0.0;
    
    for (const auto& val : data) {
        double diff = val - mean;
        sq_sum += diff * diff;
    }
    
    size_t n = data.size();
    double divisor = sample ? (n > 1 ? n - 1 : 1) : n;
    
    return std::sqrt(sq_sum / divisor);
}

/**
 * @brief 计算向量的最大值
 */
template<typename T>
T calculate_max(const std::vector<T>& data) {
    if (data.empty()) {
        throw std::invalid_argument("Cannot calculate max of empty vector");
    }
    return *std::max_element(data.begin(), data.end());
}

/**
 * @brief 计算向量的最小值
 */
template<typename T>
T calculate_min(const std::vector<T>& data) {
    if (data.empty()) {
        throw std::invalid_argument("Cannot calculate min of empty vector");
    }
    return *std::min_element(data.begin(), data.end());
}

/**
 * @brief 计算向量的中位数
 */
template<typename T>
double calculate_median(std::vector<T> data) {
    if (data.empty()) {
        throw std::invalid_argument("Cannot calculate median of empty vector");
    }
    
    std::sort(data.begin(), data.end());
    size_t n = data.size();
    
    if (n % 2 == 0) {
        return (data[n/2 - 1] + data[n/2]) / 2.0;
    } else {
        return data[n/2];
    }
}

/**
 * @brief 计算两个向量的协方差
 */
template<typename T>
double calculate_covariance(const std::vector<T>& x, const std::vector<T>& y, bool sample = true) {
    if (x.size() != y.size() || x.empty()) {
        throw std::invalid_argument("Vectors must have same non-zero size");
    }
    
    double mean_x = calculate_mean(x);
    double mean_y = calculate_mean(y);
    
    double cov = 0.0;
    for (size_t i = 0; i < x.size(); ++i) {
        cov += (x[i] - mean_x) * (y[i] - mean_y);
    }
    
    size_t n = x.size();
    double divisor = sample ? (n > 1 ? n - 1 : 1) : n;
    
    return cov / divisor;
}

/**
 * @brief 计算两个向量的相关系数
 */
template<typename T>
double calculate_correlation(const std::vector<T>& x, const std::vector<T>& y) {
    if (x.size() != y.size() || x.empty()) {
        throw std::invalid_argument("Vectors must have same non-zero size");
    }
    
    double cov = calculate_covariance(x, y);
    double std_x = calculate_std(x);
    double std_y = calculate_std(y);
    
    if (std_x == 0.0 || std_y == 0.0) {
        return 0.0;
    }
    
    return cov / (std_x * std_y);
}

/**
 * @brief 计算向量的累积和
 */
template<typename T>
std::vector<double> cumulative_sum(const std::vector<T>& data) {
    std::vector<double> result;
    result.reserve(data.size());
    
    double sum = 0.0;
    for (const auto& val : data) {
        sum += val;
        result.push_back(sum);
    }
    
    return result;
}

/**
 * @brief 计算向量的滚动均值
 */
template<typename T>
std::vector<double> rolling_mean(const std::vector<T>& data, size_t window) {
    if (window == 0 || window > data.size()) {
        throw std::invalid_argument("Invalid window size");
    }
    
    std::vector<double> result;
    result.reserve(data.size() - window + 1);
    
    for (size_t i = 0; i <= data.size() - window; ++i) {
        double sum = 0.0;
        for (size_t j = i; j < i + window; ++j) {
            sum += data[j];
        }
        result.push_back(sum / window);
    }
    
    return result;
}

/**
 * @brief 计算百分比变化
 */
template<typename T>
std::vector<double> pct_change(const std::vector<T>& data) {
    if (data.size() < 2) {
        return std::vector<double>();
    }
    
    std::vector<double> result;
    result.reserve(data.size() - 1);
    
    for (size_t i = 1; i < data.size(); ++i) {
        if (data[i-1] != 0) {
            result.push_back((data[i] - data[i-1]) / data[i-1]);
        } else {
            result.push_back(0.0);
        }
    }
    
    return result;
}

} // namespace utils
} // namespace apexquant

