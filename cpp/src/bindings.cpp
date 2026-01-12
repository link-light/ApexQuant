#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>

#include "data_structures.h"
#include "utils.h"
#include "indicators.h"

namespace py = pybind11;
using namespace apexquant;

PYBIND11_MODULE(apexquant_core, m) {
    m.doc() = "ApexQuant C++ Core Module - 高性能量化交易核心引擎";
    
    // ==================== 数据结构绑定 ====================
    
    // Tick 结构
    py::class_<Tick>(m, "Tick", "Tick 行情数据结构")
        .def(py::init<>(), "默认构造函数")
        .def(py::init<const std::string&, int64_t, double, double, double, int64_t>(),
             py::arg("symbol"), py::arg("timestamp"), py::arg("last_price"),
             py::arg("bid_price"), py::arg("ask_price"), py::arg("volume"),
             "构造 Tick 数据")
        .def_readwrite("symbol", &Tick::symbol, "证券代码")
        .def_readwrite("timestamp", &Tick::timestamp, "时间戳（毫秒）")
        .def_readwrite("last_price", &Tick::last_price, "最新价")
        .def_readwrite("bid_price", &Tick::bid_price, "买一价")
        .def_readwrite("ask_price", &Tick::ask_price, "卖一价")
        .def_readwrite("volume", &Tick::volume, "成交量")
        .def_readwrite("amount", &Tick::amount, "成交额")
        .def_readwrite("bid_prices", &Tick::bid_prices, "买价列表")
        .def_readwrite("bid_volumes", &Tick::bid_volumes, "买量列表")
        .def_readwrite("ask_prices", &Tick::ask_prices, "卖价列表")
        .def_readwrite("ask_volumes", &Tick::ask_volumes, "卖量列表")
        .def("mid_price", &Tick::mid_price, "获取中间价")
        .def("spread", &Tick::spread, "获取买卖价差")
        .def("__repr__", [](const Tick& t) {
            return "<Tick " + t.symbol + " last=" + std::to_string(t.last_price) + ">";
        });
    
    // Bar 结构
    py::class_<Bar>(m, "Bar", "Bar K线数据结构")
        .def(py::init<>(), "默认构造函数")
        .def(py::init<const std::string&, int64_t, double, double, double, double, int64_t>(),
             py::arg("symbol"), py::arg("timestamp"), py::arg("open"),
             py::arg("high"), py::arg("low"), py::arg("close"), py::arg("volume"),
             "构造 Bar 数据")
        .def_readwrite("symbol", &Bar::symbol, "证券代码")
        .def_readwrite("timestamp", &Bar::timestamp, "时间戳（毫秒）")
        .def_readwrite("open", &Bar::open, "开盘价")
        .def_readwrite("high", &Bar::high, "最高价")
        .def_readwrite("low", &Bar::low, "最低价")
        .def_readwrite("close", &Bar::close, "收盘价")
        .def_readwrite("volume", &Bar::volume, "成交量")
        .def_readwrite("amount", &Bar::amount, "成交额")
        .def_readwrite("trade_count", &Bar::trade_count, "成交笔数")
        .def("change_rate", &Bar::change_rate, "获取涨跌幅")
        .def("is_bullish", &Bar::is_bullish, "是否为阳线")
        .def("body_size", &Bar::body_size, "实体大小")
        .def("upper_shadow", &Bar::upper_shadow, "上影线长度")
        .def("lower_shadow", &Bar::lower_shadow, "下影线长度")
        .def("__repr__", [](const Bar& b) {
            return "<Bar " + b.symbol + " OHLC=[" + 
                   std::to_string(b.open) + "," + std::to_string(b.high) + "," +
                   std::to_string(b.low) + "," + std::to_string(b.close) + "]>";
        })
        .def("__str__", [](const Bar& b) {
            std::ostringstream oss;
            oss << b;
            return oss.str();
        });
    
    // Position 结构
    py::class_<Position>(m, "Position", "持仓数据结构")
        .def(py::init<>(), "默认构造函数")
        .def(py::init<const std::string&, int64_t, double>(),
             py::arg("symbol"), py::arg("quantity"), py::arg("avg_price"),
             "构造持仓数据")
        .def_readwrite("symbol", &Position::symbol, "证券代码")
        .def_readwrite("quantity", &Position::quantity, "持仓数量")
        .def_readwrite("avg_price", &Position::avg_price, "平均成本价")
        .def_readwrite("market_value", &Position::market_value, "市值")
        .def_readwrite("unrealized_pnl", &Position::unrealized_pnl, "未实现盈亏")
        .def_readwrite("realized_pnl", &Position::realized_pnl, "已实现盈亏")
        .def_readwrite("open_timestamp", &Position::open_timestamp, "开仓时间戳")
        .def("update_market_value", &Position::update_market_value,
             py::arg("current_price"), "更新市值和未实现盈亏")
        .def("is_long", &Position::is_long, "是否为多头")
        .def("is_short", &Position::is_short, "是否为空头")
        .def("is_flat", &Position::is_flat, "是否为空仓")
        .def("__repr__", [](const Position& p) {
            return "<Position " + p.symbol + " qty=" + std::to_string(p.quantity) + 
                   " pnl=" + std::to_string(p.unrealized_pnl) + ">";
        })
        .def("__str__", [](const Position& p) {
            std::ostringstream oss;
            oss << p;
            return oss.str();
        });
    
    // OrderSide 枚举
    py::enum_<OrderSide>(m, "OrderSide", "订单方向")
        .value("BUY", OrderSide::BUY, "买入")
        .value("SELL", OrderSide::SELL, "卖出")
        .export_values();
    
    // OrderType 枚举
    py::enum_<OrderType>(m, "OrderType", "订单类型")
        .value("MARKET", OrderType::MARKET, "市价单")
        .value("LIMIT", OrderType::LIMIT, "限价单")
        .value("STOP", OrderType::STOP, "止损单")
        .value("STOP_LIMIT", OrderType::STOP_LIMIT, "止损限价单")
        .export_values();
    
    // OrderStatus 枚举
    py::enum_<OrderStatus>(m, "OrderStatus", "订单状态")
        .value("PENDING", OrderStatus::PENDING, "待提交")
        .value("SUBMITTED", OrderStatus::SUBMITTED, "已提交")
        .value("PARTIAL_FILLED", OrderStatus::PARTIAL_FILLED, "部分成交")
        .value("FILLED", OrderStatus::FILLED, "完全成交")
        .value("CANCELLED", OrderStatus::CANCELLED, "已撤销")
        .value("REJECTED", OrderStatus::REJECTED, "已拒绝")
        .export_values();
    
    // Order 结构
    py::class_<Order>(m, "Order", "订单数据结构")
        .def(py::init<>(), "默认构造函数")
        .def(py::init<const std::string&, OrderSide, int64_t, double>(),
             py::arg("symbol"), py::arg("side"), py::arg("quantity"), 
             py::arg("price") = 0.0,
             "构造订单数据")
        .def_readwrite("order_id", &Order::order_id, "订单ID")
        .def_readwrite("symbol", &Order::symbol, "证券代码")
        .def_readwrite("side", &Order::side, "买卖方向")
        .def_readwrite("type", &Order::type, "订单类型")
        .def_readwrite("status", &Order::status, "订单状态")
        .def_readwrite("quantity", &Order::quantity, "委托数量")
        .def_readwrite("filled_quantity", &Order::filled_quantity, "已成交数量")
        .def_readwrite("price", &Order::price, "委托价格")
        .def_readwrite("filled_avg_price", &Order::filled_avg_price, "成交均价")
        .def_readwrite("create_timestamp", &Order::create_timestamp, "创建时间")
        .def_readwrite("update_timestamp", &Order::update_timestamp, "更新时间")
        .def_readwrite("strategy_id", &Order::strategy_id, "策略ID")
        .def_readwrite("comment", &Order::comment, "备注")
        .def("is_filled", &Order::is_filled, "是否完全成交")
        .def("is_active", &Order::is_active, "是否活跃")
        .def("remaining_quantity", &Order::remaining_quantity, "剩余数量")
        .def("fill_ratio", &Order::fill_ratio, "成交率")
        .def("__repr__", [](const Order& o) {
            return "<Order " + o.symbol + " " + 
                   (o.side == OrderSide::BUY ? "BUY" : "SELL") + 
                   " qty=" + std::to_string(o.quantity) + ">";
        });
    
    // ==================== 工具函数绑定 ====================
    
    // 均值计算
    m.def("calculate_mean", 
          &utils::calculate_mean<double>,
          py::arg("data"),
          "计算向量的均值\n\n参数:\n    data: 输入数据列表\n\n返回:\n    均值");
    
    m.def("calculate_mean_int", 
          &utils::calculate_mean<int>,
          py::arg("data"),
          "计算整数向量的均值");
    
    // 标准差计算
    m.def("calculate_std",
          &utils::calculate_std<double>,
          py::arg("data"), py::arg("sample") = true,
          "计算向量的标准差\n\n参数:\n    data: 输入数据列表\n    sample: 是否使用样本标准差\n\n返回:\n    标准差");
    
    // 最大值/最小值
    m.def("calculate_max",
          &utils::calculate_max<double>,
          py::arg("data"),
          "计算向量的最大值");
    
    m.def("calculate_min",
          &utils::calculate_min<double>,
          py::arg("data"),
          "计算向量的最小值");
    
    // 中位数
    m.def("calculate_median",
          &utils::calculate_median<double>,
          py::arg("data"),
          "计算向量的中位数");
    
    // 协方差
    m.def("calculate_covariance",
          &utils::calculate_covariance<double>,
          py::arg("x"), py::arg("y"), py::arg("sample") = true,
          "计算两个向量的协方差");
    
    // 相关系数
    m.def("calculate_correlation",
          &utils::calculate_correlation<double>,
          py::arg("x"), py::arg("y"),
          "计算两个向量的相关系数");
    
    // 累积和
    m.def("cumulative_sum",
          &utils::cumulative_sum<double>,
          py::arg("data"),
          "计算向量的累积和");
    
    // 滚动均值
    m.def("rolling_mean",
          &utils::rolling_mean<double>,
          py::arg("data"), py::arg("window"),
          "计算向量的滚动均值");
    
    // 百分比变化
    m.def("pct_change",
          &utils::pct_change<double>,
          py::arg("data"),
          "计算百分比变化");
    
    // ==================== 技术指标绑定 ====================
    
    auto m_indicators = m.def_submodule("indicators", "技术指标模块");
    
    // SMA
    m_indicators.def("sma",
          &indicators::sma,
          py::arg("data"), py::arg("period"),
          "简单移动平均");
    
    // EMA
    m_indicators.def("ema",
          &indicators::ema,
          py::arg("data"), py::arg("period"),
          "指数移动平均");
    
    // MACD 结果结构
    py::class_<indicators::MACDResult>(m_indicators, "MACDResult")
        .def_readonly("macd", &indicators::MACDResult::macd)
        .def_readonly("signal", &indicators::MACDResult::signal)
        .def_readonly("histogram", &indicators::MACDResult::histogram);
    
    m_indicators.def("macd",
          &indicators::macd,
          py::arg("data"), 
          py::arg("fast_period") = 12,
          py::arg("slow_period") = 26,
          py::arg("signal_period") = 9,
          "MACD 指标");
    
    // RSI
    m_indicators.def("rsi",
          &indicators::rsi,
          py::arg("data"), py::arg("period") = 14,
          "相对强弱指标");
    
    // 布林带结果结构
    py::class_<indicators::BollingerBandsResult>(m_indicators, "BollingerBandsResult")
        .def_readonly("upper", &indicators::BollingerBandsResult::upper)
        .def_readonly("middle", &indicators::BollingerBandsResult::middle)
        .def_readonly("lower", &indicators::BollingerBandsResult::lower);
    
    m_indicators.def("bollinger_bands",
          &indicators::bollinger_bands,
          py::arg("data"), 
          py::arg("period") = 20,
          py::arg("num_std") = 2.0,
          "布林带");
    
    // KDJ 结果结构
    py::class_<indicators::KDJResult>(m_indicators, "KDJResult")
        .def_readonly("k", &indicators::KDJResult::k)
        .def_readonly("d", &indicators::KDJResult::d)
        .def_readonly("j", &indicators::KDJResult::j);
    
    m_indicators.def("kdj",
          &indicators::kdj,
          py::arg("high"), py::arg("low"), py::arg("close"),
          py::arg("period") = 9,
          py::arg("k_smooth") = 3,
          py::arg("d_smooth") = 3,
          "KDJ 指标");
    
    // ATR
    m_indicators.def("atr",
          &indicators::atr,
          py::arg("high"), py::arg("low"), py::arg("close"),
          py::arg("period") = 14,
          "平均真实波动范围");
    
    // OBV
    m_indicators.def("obv",
          &indicators::obv,
          py::arg("close"), py::arg("volume"),
          "能量潮");
    
    // Momentum
    m_indicators.def("momentum",
          &indicators::momentum,
          py::arg("data"), py::arg("period") = 10,
          "动量指标");
    
    // ROC
    m_indicators.def("roc",
          &indicators::roc,
          py::arg("data"), py::arg("period") = 10,
          "变动率");
    
    // Williams %R
    m_indicators.def("williams_r",
          &indicators::williams_r,
          py::arg("high"), py::arg("low"), py::arg("close"),
          py::arg("period") = 14,
          "威廉指标");
    
    // 版本信息
    m.attr("__version__") = "1.0.0";
    m.attr("__author__") = "ApexQuant Team";
}

