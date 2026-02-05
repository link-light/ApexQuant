/**
 * @file bindings.cpp
 * @brief ApexQuant模拟盘模块的pybind11 Python绑定
 * 
 * 将C++模拟盘类暴露给Python
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>

#include "simulation/simulation_types.h"
#include "simulation/simulation_account.h"
#include "simulation/order_matcher.h"
#include "simulation/simulated_exchange.h"
#include "data_structures.h"  // 主项目的Tick定义

namespace py = pybind11;
using namespace apexquant;
using namespace apexquant::simulation;

PYBIND11_MODULE(apexquant_simulation, m) {
    m.doc() = "ApexQuant Simulation Trading Module";
    
    // ========================================================================
    // 枚举类型（使用simulation命名空间）
    // ========================================================================
    
    py::enum_<simulation::OrderSide>(m, "OrderSide", "Order side enum")
        .value("BUY", simulation::OrderSide::BUY, "Buy order")
        .value("SELL", simulation::OrderSide::SELL, "Sell order")
        .export_values();
    
    py::enum_<simulation::OrderType>(m, "OrderType", "Order type enum")
        .value("MARKET", simulation::OrderType::MARKET, "Market order")
        .value("LIMIT", simulation::OrderType::LIMIT, "Limit order")
        .export_values();
    
    py::enum_<simulation::OrderStatus>(m, "OrderStatus", "Order status enum")
        .value("PENDING", simulation::OrderStatus::PENDING, "Pending")
        .value("PARTIAL_FILLED", simulation::OrderStatus::PARTIAL_FILLED, "Partially filled")
        .value("FILLED", simulation::OrderStatus::FILLED, "Completely filled")
        .value("CANCELLED", simulation::OrderStatus::CANCELLED, "Cancelled")
        .value("REJECTED", simulation::OrderStatus::REJECTED, "Rejected")
        .export_values();
    
    // ========================================================================
    // 结构体 - SimulatedOrder
    // ========================================================================
    
    py::class_<SimulatedOrder>(m, "SimulatedOrder", "Simulated order")
        .def(py::init<>())
        .def(py::init<const std::string&, const std::string&, simulation::OrderSide, simulation::OrderType, 
                     double, int64_t, int64_t>(),
             py::arg("order_id"),
             py::arg("symbol"),
             py::arg("side"),
             py::arg("type"),
             py::arg("price"),
             py::arg("volume"),
             py::arg("submit_time"))
        .def_readwrite("order_id", &SimulatedOrder::order_id, "Order ID")
        .def_readwrite("symbol", &SimulatedOrder::symbol, "Symbol")
        .def_readwrite("side", &SimulatedOrder::side, "Order side")
        .def_readwrite("type", &SimulatedOrder::type, "Order type")
        .def_readwrite("price", &SimulatedOrder::price, "Price")
        .def_readwrite("volume", &SimulatedOrder::volume, "Volume")
        .def_readwrite("filled_volume", &SimulatedOrder::filled_volume, "Filled volume")
        .def_readwrite("status", &SimulatedOrder::status, "Order status")
        .def_readwrite("submit_time", &SimulatedOrder::submit_time, "Submit time")
        .def_readwrite("commission_rate", &SimulatedOrder::commission_rate, "Commission rate")
        .def_readwrite("slippage_rate", &SimulatedOrder::slippage_rate, "Slippage rate")
        .def("__repr__", &SimulatedOrder::toString);
    
    // ========================================================================
    // 结构体 - Position（使用simulation命名空间）
    // ========================================================================
    
    py::class_<simulation::Position>(m, "Position", "Position information")
        .def(py::init<>())
        .def(py::init<const std::string&, int64_t, double, int64_t>(),
             py::arg("symbol"),
             py::arg("volume"),
             py::arg("cost"),
             py::arg("buy_date"))
        .def_readonly("symbol", &simulation::Position::symbol, "Symbol")
        .def_readonly("volume", &simulation::Position::volume, "Total volume")
        .def_readonly("available_volume", &simulation::Position::available_volume, "Available volume (T+1)")
        .def_readonly("frozen_volume", &simulation::Position::frozen_volume, "Frozen volume")
        .def_readonly("avg_cost", &simulation::Position::avg_cost, "Average cost")
        .def_readonly("current_price", &simulation::Position::current_price, "Current price")
        .def_readonly("market_value", &simulation::Position::market_value, "Market value")
        .def_readonly("unrealized_pnl", &simulation::Position::unrealized_pnl, "Unrealized PnL")
        .def_readonly("buy_date", &simulation::Position::buy_date, "Buy date (YYYYMMDD)")
        .def("__repr__", &simulation::Position::toString);
    
    // ========================================================================
    // 结构体 - TradeRecord
    // ========================================================================
    
    py::class_<TradeRecord>(m, "TradeRecord", "Trade record")
        .def(py::init<>())
        .def(py::init<const std::string&, const std::string&, const std::string&,
                     simulation::OrderSide, double, int64_t, double, int64_t>(),
             py::arg("trade_id"),
             py::arg("order_id"),
             py::arg("symbol"),
             py::arg("side"),
             py::arg("price"),
             py::arg("volume"),
             py::arg("commission"),
             py::arg("trade_time"))
        .def_readonly("trade_id", &TradeRecord::trade_id, "Trade ID")
        .def_readonly("order_id", &TradeRecord::order_id, "Order ID")
        .def_readonly("symbol", &TradeRecord::symbol, "Symbol")
        .def_readonly("side", &TradeRecord::side, "Side")
        .def_readonly("price", &TradeRecord::price, "Price")
        .def_readonly("volume", &TradeRecord::volume, "Volume")
        .def_readonly("commission", &TradeRecord::commission, "Commission")
        .def_readonly("trade_time", &TradeRecord::trade_time, "Trade time")
        .def_readonly("realized_pnl", &TradeRecord::realized_pnl, "Realized PnL")
        .def("__repr__", &TradeRecord::toString);
    
    // ========================================================================
    // 结构体 - MatchResult
    // ========================================================================
    
    py::class_<MatchResult>(m, "MatchResult", "Match result")
        .def(py::init<>())
        .def(py::init<double, int64_t>(),
             py::arg("filled_price"),
             py::arg("filled_volume"))
        .def(py::init<const std::string&>(),
             py::arg("reject_reason"))
        .def_readonly("success", &MatchResult::success, "Match success")
        .def_readonly("filled_price", &MatchResult::filled_price, "Filled price")
        .def_readonly("filled_volume", &MatchResult::filled_volume, "Filled volume")
        .def_readonly("reject_reason", &MatchResult::reject_reason, "Reject reason")
        .def("__repr__", &MatchResult::toString);
    
    // ========================================================================
    // Tick类型说明
    // ========================================================================
    // Tick类型已在apexquant_core模块中注册，simulation模块直接使用
    // 无需重复绑定，避免"type already registered"错误
    
    // ========================================================================
    // 主类 - SimulatedExchange
    // ========================================================================
    
    py::class_<SimulatedExchange>(m, "SimulatedExchange", "Simulated exchange")
        .def(py::init<const std::string&, double>(),
             py::arg("account_id"),
             py::arg("initial_capital"),
             "Create a simulated exchange\n\n"
             "Args:\n"
             "    account_id: Account ID\n"
             "    initial_capital: Initial capital")
        
        // 订单管理
        .def("submit_order", &SimulatedExchange::submit_order,
             py::arg("order"),
             "Submit an order\n\n"
             "Args:\n"
             "    order: SimulatedOrder object\n\n"
             "Returns:\n"
             "    Order ID")
        
        .def("on_tick", &SimulatedExchange::on_tick,
             py::arg("tick"),
             "Process market tick and try to match orders\n\n"
             "Args:\n"
             "    tick: Tick object")
        
        .def("cancel_order", &SimulatedExchange::cancel_order,
             py::arg("order_id"),
             "Cancel an order\n\n"
             "Args:\n"
             "    order_id: Order ID\n\n"
             "Returns:\n"
             "    True if cancelled successfully")
        
        // 查询方法
        .def("get_order", &SimulatedExchange::get_order,
             py::arg("order_id"),
             "Get order by ID")
        
        .def("get_pending_orders", 
             py::overload_cast<>(&SimulatedExchange::get_pending_orders, py::const_),
             "Get all pending orders")
        
        .def("get_pending_orders", 
             py::overload_cast<const std::string&>(&SimulatedExchange::get_pending_orders, py::const_),
             py::arg("symbol"),
             "Get pending orders for a symbol")
        
        .def("get_trade_history", &SimulatedExchange::get_trade_history,
             "Get all trade history")
        
        .def("get_position", &SimulatedExchange::get_position,
             py::arg("symbol"),
             "Get position for a symbol")
        
        .def("get_all_positions", &SimulatedExchange::get_all_positions,
             "Get all positions")
        
        .def("get_total_assets", &SimulatedExchange::get_total_assets,
             "Get total assets (cash + market value)")
        
        .def("get_available_cash", &SimulatedExchange::get_available_cash,
             "Get available cash")
        
        .def("get_frozen_cash", &SimulatedExchange::get_frozen_cash,
             "Get frozen cash")
        
        // 日常维护
        .def("update_daily", &SimulatedExchange::update_daily,
             py::arg("current_date"),
             "Update daily, unlock T+1 positions\n\n"
             "Args:\n"
             "    current_date: Current date (format: 20250203)")
        
        .def("get_account_id", &SimulatedExchange::get_account_id,
             "Get account ID");
    
    // ========================================================================
    // 辅助类（可选）
    // ========================================================================
    
    py::class_<OrderMatcher>(m, "OrderMatcher", "Order matcher engine")
        .def(py::init<double, double, double>(),
             py::arg("default_slippage_rate") = 0.0001,
             py::arg("default_commission_rate") = 0.00025,
             py::arg("stamp_tax_rate") = 0.001,
             "Create an order matcher\n\n"
             "Args:\n"
             "    default_slippage_rate: Default slippage rate (default 0.0001)\n"
             "    default_commission_rate: Default commission rate (default 0.00025)\n"
             "    stamp_tax_rate: Stamp tax rate for selling (default 0.001)")
        
        .def("try_match_order", &OrderMatcher::try_match_order,
             py::arg("order"),
             py::arg("current_tick"),
             py::arg("check_price_limit") = true,
             "Try to match an order")
        
        .def("check_limit_price", &OrderMatcher::check_limit_price,
             py::arg("symbol"),
             py::arg("price"),
             py::arg("last_close"),
             "Check if price is within limit price range")
        
        .def("calculate_slippage", &OrderMatcher::calculate_slippage,
             py::arg("side"),
             py::arg("base_price"),
             py::arg("volume"),
             py::arg("slippage_rate"),
             "Calculate slippage price")
        
        .def("check_liquidity", &OrderMatcher::check_liquidity,
             py::arg("volume"),
             py::arg("tick"),
             py::arg("side"),
             "Check if there is sufficient liquidity");
    
    // 版本信息
    m.attr("__version__") = "1.0.0";
}
