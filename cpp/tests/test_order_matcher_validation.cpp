/**
 * @file test_order_matcher_validation.cpp
 * @brief 测试订单撮合器的输入验证和异常处理
 */

#include <catch2/catch_test_macros.hpp>
#include "simulation/order_matcher.h"

using namespace apexquant::simulation;

TEST_CASE("OrderMatcher input validation", "[order_matcher][validation]") {
    OrderMatcher matcher(0.001, 0.0003, 0.001);
    
    // 创建有效的tick数据
    Tick valid_tick;
    valid_tick.symbol = "600519.SH";
    valid_tick.last_price = 100.0;
    valid_tick.ask_price = 100.1;
    valid_tick.bid_price = 99.9;
    valid_tick.volume = 1000000;
    valid_tick.last_close = 99.0;
    
    SECTION("Rejects zero volume") {
        SimulatedOrder order;
        order.symbol = "600519.SH";
        order.side = OrderSide::BUY;
        order.type = OrderType::MARKET;
        order.volume = 0;  // 无效：零数量
        order.price = 0.0;
        
        auto result = matcher.try_match_order(order, valid_tick, false);
        
        REQUIRE(result.success == false);
        REQUIRE(result.reject_reason.find("volume") != std::string::npos);
    }
    
    SECTION("Rejects negative volume") {
        SimulatedOrder order;
        order.symbol = "600519.SH";
        order.side = OrderSide::BUY;
        order.type = OrderType::MARKET;
        order.volume = -100;  // 无效：负数量
        order.price = 0.0;
        
        auto result = matcher.try_match_order(order, valid_tick, false);
        
        REQUIRE(result.success == false);
    }
    
    SECTION("Rejects excessive volume") {
        SimulatedOrder order;
        order.symbol = "600519.SH";
        order.side = OrderSide::BUY;
        order.type = OrderType::MARKET;
        order.volume = 2000000000;  // 无效：超过10亿股
        order.price = 0.0;
        
        auto result = matcher.try_match_order(order, valid_tick, false);
        
        REQUIRE(result.success == false);
        REQUIRE(result.reject_reason.find("maximum") != std::string::npos);
    }
    
    SECTION("Rejects invalid tick price") {
        SimulatedOrder order;
        order.symbol = "600519.SH";
        order.side = OrderSide::BUY;
        order.type = OrderType::MARKET;
        order.volume = 100;
        order.price = 0.0;
        
        Tick invalid_tick = valid_tick;
        invalid_tick.last_price = 0.0;  // 无效：零价格
        
        auto result = matcher.try_match_order(order, invalid_tick, false);
        
        REQUIRE(result.success == false);
        REQUIRE(result.reject_reason.find("tick price") != std::string::npos);
    }
    
    SECTION("Rejects invalid limit price") {
        SimulatedOrder order;
        order.symbol = "600519.SH";
        order.side = OrderSide::BUY;
        order.type = OrderType::LIMIT;
        order.volume = 100;
        order.price = -10.0;  // 无效：负价格
        
        auto result = matcher.try_match_order(order, valid_tick, false);
        
        REQUIRE(result.success == false);
        REQUIRE(result.reject_reason.find("limit price") != std::string::npos);
    }
    
    SECTION("Accepts valid market order") {
        SimulatedOrder order;
        order.symbol = "600519.SH";
        order.side = OrderSide::BUY;
        order.type = OrderType::MARKET;
        order.volume = 100;
        order.price = 0.0;
        
        auto result = matcher.try_match_order(order, valid_tick, false);
        
        REQUIRE(result.success == true);
        REQUIRE(result.filled_volume == 100);
        REQUIRE(result.filled_price > 0.0);
    }
}

TEST_CASE("OrderMatcher check_limit_price validation", "[order_matcher][validation]") {
    OrderMatcher matcher(0.001, 0.0003, 0.001);
    
    SECTION("Rejects zero last_close") {
        bool result = matcher.check_limit_price("600519.SH", 100.0, 0.0);
        REQUIRE(result == false);
    }
    
    SECTION("Rejects negative last_close") {
        bool result = matcher.check_limit_price("600519.SH", 100.0, -99.0);
        REQUIRE(result == false);
    }
    
    SECTION("Rejects zero price") {
        bool result = matcher.check_limit_price("600519.SH", 0.0, 99.0);
        REQUIRE(result == false);
    }
    
    SECTION("Rejects negative price") {
        bool result = matcher.check_limit_price("600519.SH", -100.0, 99.0);
        REQUIRE(result == false);
    }
    
    SECTION("Accepts valid prices within limit") {
        bool result = matcher.check_limit_price("600519.SH", 105.0, 100.0);
        REQUIRE(result == true);
    }
}

TEST_CASE("OrderMatcher calculate_slippage validation", "[order_matcher][validation]") {
    OrderMatcher matcher(0.001, 0.0003, 0.001);
    
    SECTION("Handles zero base_price") {
        double result = matcher.calculate_slippage(
            OrderSide::BUY, 
            0.0,  // 无效：零价格
            100, 
            0.001
        );
        REQUIRE(result == 0.0);  // 返回原值
    }
    
    SECTION("Handles negative base_price") {
        double result = matcher.calculate_slippage(
            OrderSide::BUY, 
            -100.0,  // 无效：负价格
            100, 
            0.001
        );
        REQUIRE(result == -100.0);  // 返回原值
    }
    
    SECTION("Handles invalid slippage_rate") {
        double result = matcher.calculate_slippage(
            OrderSide::BUY, 
            100.0, 
            100, 
            -0.5  // 无效：负滑点率
        );
        // 应该使用默认值0.1%
        REQUIRE(result > 100.0);
        REQUIRE(result < 101.0);
    }
    
    SECTION("Calculates valid slippage") {
        double result = matcher.calculate_slippage(
            OrderSide::BUY, 
            100.0, 
            100, 
            0.001
        );
        REQUIRE(result > 100.0);  // 买入应该有正滑点
    }
}

