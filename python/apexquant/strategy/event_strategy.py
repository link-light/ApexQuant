"""
事件驱动策略

包含财报发布、股东增减持、大宗交易等事件驱动的交易策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""
    EARNINGS = "earnings"           # 财报发布
    HOLDER_CHANGE = "holder_change" # 股东增减持
    BLOCK_TRADE = "block_trade"     # 大宗交易
    DIVIDEND = "dividend"           # 分红派息
    STOCK_SPLIT = "stock_split"     # 股票拆分
    BUYBACK = "buyback"             # 股票回购
    INSIDER = "insider"             # 内部人交易
    RATING = "rating"               # 评级变动
    NEWS = "news"                   # 重大新闻


@dataclass
class Event:
    """事件"""
    event_type: EventType
    symbol: str
    date: datetime
    title: str
    content: str = ""
    impact_score: float = 0.0  # -1到1，负面到正面
    confidence: float = 0.5
    data: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'event_type': self.event_type.value,
            'symbol': self.symbol,
            'date': self.date.isoformat() if self.date else None,
            'title': self.title,
            'content': self.content,
            'impact_score': self.impact_score,
            'confidence': self.confidence,
            'data': self.data
        }


@dataclass
class EventSignal:
    """事件信号"""
    symbol: str
    event: Event
    signal: str  # 'buy', 'sell', 'hold'
    strength: float  # 信号强度 0-1
    entry_window: int  # 建议入场时间窗口（天）
    holding_period: int  # 建议持有期（天）
    stop_loss: float  # 止损比例
    take_profit: float  # 止盈比例
    reason: str

    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'event': self.event.to_dict(),
            'signal': self.signal,
            'strength': self.strength,
            'entry_window': self.entry_window,
            'holding_period': self.holding_period,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'reason': self.reason
        }


class EarningsStrategy:
    """财报策略"""

    def __init__(self):
        # 历史统计参数
        self.beat_avg_return = 2.5  # 超预期平均收益率%
        self.miss_avg_return = -3.0  # 不及预期平均收益率%

    def analyze_earnings(self, event: Event,
                        historical_earnings: Optional[List[Dict]] = None) -> EventSignal:
        """
        分析财报事件

        Args:
            event: 财报事件
            historical_earnings: 历史财报数据

        Returns:
            事件信号
        """
        data = event.data

        # 获取关键指标
        revenue_growth = data.get('revenue_growth', 0)
        profit_growth = data.get('profit_growth', 0)
        eps_actual = data.get('eps_actual', 0)
        eps_estimate = data.get('eps_estimate', 0)
        revenue_actual = data.get('revenue_actual', 0)
        revenue_estimate = data.get('revenue_estimate', 0)

        # 计算超预期程度
        eps_surprise = 0
        if eps_estimate and eps_estimate != 0:
            eps_surprise = (eps_actual - eps_estimate) / abs(eps_estimate) * 100

        revenue_surprise = 0
        if revenue_estimate and revenue_estimate != 0:
            revenue_surprise = (revenue_actual - revenue_estimate) / abs(revenue_estimate) * 100

        # 综合评分
        score = 0

        # EPS超预期
        if eps_surprise > 10:
            score += 2
        elif eps_surprise > 5:
            score += 1
        elif eps_surprise < -10:
            score -= 2
        elif eps_surprise < -5:
            score -= 1

        # 营收超预期
        if revenue_surprise > 5:
            score += 1
        elif revenue_surprise < -5:
            score -= 1

        # 增长率
        if profit_growth > 30:
            score += 1
        elif profit_growth < 0:
            score -= 1

        if revenue_growth > 20:
            score += 0.5
        elif revenue_growth < 0:
            score -= 0.5

        # 确定信号
        if score >= 2:
            signal = 'buy'
            strength = min(1.0, score / 4)
            reason = f"财报超预期: EPS超{eps_surprise:.1f}%, 营收超{revenue_surprise:.1f}%"
        elif score <= -2:
            signal = 'sell'
            strength = min(1.0, abs(score) / 4)
            reason = f"财报不及预期: EPS低于预期{abs(eps_surprise):.1f}%"
        else:
            signal = 'hold'
            strength = 0.3
            reason = "财报符合预期，无明显信号"

        return EventSignal(
            symbol=event.symbol,
            event=event,
            signal=signal,
            strength=strength,
            entry_window=2,  # 财报后2天内建仓
            holding_period=20,  # 持有20天
            stop_loss=0.05,
            take_profit=0.10,
            reason=reason
        )

    def pre_earnings_strategy(self, symbol: str,
                             earnings_date: datetime,
                             historical_beats: int = 4,
                             total_quarters: int = 8) -> EventSignal:
        """
        财报前策略（赌财报）

        Args:
            symbol: 股票代码
            earnings_date: 财报日期
            historical_beats: 历史超预期次数
            total_quarters: 统计季度数

        Returns:
            事件信号
        """
        beat_ratio = historical_beats / total_quarters if total_quarters > 0 else 0.5

        event = Event(
            event_type=EventType.EARNINGS,
            symbol=symbol,
            date=earnings_date,
            title="财报发布预期",
            content=f"即将发布财报，历史{total_quarters}个季度超预期{historical_beats}次",
            impact_score=beat_ratio - 0.5,
            confidence=0.6
        )

        # 超预期概率高则买入
        if beat_ratio > 0.7:
            signal = 'buy'
            strength = min(1.0, (beat_ratio - 0.5) * 2)
            reason = f"历史超预期率{beat_ratio*100:.0f}%，财报前建仓"
        elif beat_ratio < 0.3:
            signal = 'sell'
            strength = min(1.0, (0.5 - beat_ratio) * 2)
            reason = f"历史超预期率仅{beat_ratio*100:.0f}%，财报前减仓"
        else:
            signal = 'hold'
            strength = 0.3
            reason = "历史超预期率一般，观望"

        return EventSignal(
            symbol=symbol,
            event=event,
            signal=signal,
            strength=strength,
            entry_window=5,  # 财报前5天
            holding_period=3,  # 持有到财报后3天
            stop_loss=0.03,
            take_profit=0.08,
            reason=reason
        )


class HolderChangeStrategy:
    """股东增减持策略"""

    def analyze_holder_change(self, event: Event) -> EventSignal:
        """
        分析股东增减持

        Args:
            event: 增减持事件

        Returns:
            事件信号
        """
        data = event.data

        holder_type = data.get('holder_type', 'unknown')  # 'major', 'executive', 'fund'
        change_type = data.get('change_type', 'unknown')  # 'increase', 'decrease'
        change_ratio = data.get('change_ratio', 0)  # 变动比例%
        change_amount = data.get('change_amount', 0)  # 变动金额

        score = 0

        # 根据股东类型评分
        type_weight = {
            'major': 2.0,      # 大股东
            'executive': 1.5,  # 高管
            'fund': 1.0,       # 基金
            'unknown': 0.5
        }
        weight = type_weight.get(holder_type, 0.5)

        # 根据变动方向和幅度评分
        if change_type == 'increase':
            if change_ratio > 5:
                score = 3 * weight
            elif change_ratio > 2:
                score = 2 * weight
            elif change_ratio > 0.5:
                score = 1 * weight
        elif change_type == 'decrease':
            if change_ratio > 5:
                score = -3 * weight
            elif change_ratio > 2:
                score = -2 * weight
            elif change_ratio > 0.5:
                score = -1 * weight

        # 确定信号
        if score >= 2:
            signal = 'buy'
            strength = min(1.0, score / 6)
            reason = f"{holder_type}增持{change_ratio:.1f}%，看好公司发展"
        elif score <= -2:
            signal = 'sell'
            strength = min(1.0, abs(score) / 6)
            reason = f"{holder_type}减持{change_ratio:.1f}%，注意风险"
        else:
            signal = 'hold'
            strength = 0.3
            reason = "增减持幅度较小，影响有限"

        return EventSignal(
            symbol=event.symbol,
            event=event,
            signal=signal,
            strength=strength,
            entry_window=3,
            holding_period=30,
            stop_loss=0.05,
            take_profit=0.15,
            reason=reason
        )


class BlockTradeStrategy:
    """大宗交易策略"""

    def analyze_block_trade(self, event: Event,
                           recent_avg_volume: float = 0) -> EventSignal:
        """
        分析大宗交易

        Args:
            event: 大宗交易事件
            recent_avg_volume: 近期日均成交额

        Returns:
            事件信号
        """
        data = event.data

        trade_amount = data.get('trade_amount', 0)  # 成交金额
        trade_price = data.get('trade_price', 0)    # 成交价
        close_price = data.get('close_price', 0)    # 收盘价
        discount_rate = data.get('discount_rate', 0)  # 折价率%

        # 计算溢价/折价
        if close_price and trade_price:
            premium = (trade_price / close_price - 1) * 100
        else:
            premium = -discount_rate

        # 成交量相对规模
        volume_ratio = 0
        if recent_avg_volume > 0:
            volume_ratio = trade_amount / recent_avg_volume

        score = 0

        # 溢价大宗交易是利好
        if premium > 0:
            score += min(2, premium / 2)
        elif premium < -5:
            score -= min(2, abs(premium) / 3)

        # 大额交易影响大
        if volume_ratio > 3:
            score = score * 1.5
        elif volume_ratio < 0.5:
            score = score * 0.5

        if score >= 1:
            signal = 'buy'
            strength = min(1.0, score / 3)
            reason = f"大宗交易溢价{premium:.1f}%，机构看好"
        elif score <= -1:
            signal = 'sell'
            strength = min(1.0, abs(score) / 3)
            reason = f"大宗交易折价{abs(premium):.1f}%，注意风险"
        else:
            signal = 'hold'
            strength = 0.3
            reason = "大宗交易价格接近市价，影响有限"

        return EventSignal(
            symbol=event.symbol,
            event=event,
            signal=signal,
            strength=strength,
            entry_window=1,
            holding_period=5,
            stop_loss=0.03,
            take_profit=0.05,
            reason=reason
        )


class EventDrivenStrategy:
    """事件驱动综合策略"""

    def __init__(self):
        self.earnings_strategy = EarningsStrategy()
        self.holder_strategy = HolderChangeStrategy()
        self.block_strategy = BlockTradeStrategy()

    def analyze_event(self, event: Event,
                     context: Optional[Dict] = None) -> EventSignal:
        """
        分析事件

        Args:
            event: 事件
            context: 上下文数据

        Returns:
            事件信号
        """
        context = context or {}

        if event.event_type == EventType.EARNINGS:
            return self.earnings_strategy.analyze_earnings(event)
        elif event.event_type == EventType.HOLDER_CHANGE:
            return self.holder_strategy.analyze_holder_change(event)
        elif event.event_type == EventType.BLOCK_TRADE:
            return self.block_strategy.analyze_block_trade(
                event, context.get('recent_avg_volume', 0)
            )
        else:
            # 默认处理
            return self._default_analysis(event)

    def _default_analysis(self, event: Event) -> EventSignal:
        """默认事件分析"""
        # 基于impact_score判断
        if event.impact_score > 0.3:
            signal = 'buy'
            strength = min(1.0, event.impact_score)
        elif event.impact_score < -0.3:
            signal = 'sell'
            strength = min(1.0, abs(event.impact_score))
        else:
            signal = 'hold'
            strength = 0.3

        return EventSignal(
            symbol=event.symbol,
            event=event,
            signal=signal,
            strength=strength * event.confidence,
            entry_window=3,
            holding_period=10,
            stop_loss=0.05,
            take_profit=0.10,
            reason=event.title
        )

    def analyze_multiple_events(self, events: List[Event],
                               symbol: str) -> EventSignal:
        """
        分析多个事件

        Args:
            events: 事件列表
            symbol: 股票代码

        Returns:
            综合信号
        """
        if not events:
            dummy_event = Event(
                event_type=EventType.NEWS,
                symbol=symbol,
                date=datetime.now(),
                title="无事件",
                impact_score=0,
                confidence=0
            )
            return EventSignal(
                symbol=symbol,
                event=dummy_event,
                signal='hold',
                strength=0,
                entry_window=0,
                holding_period=0,
                stop_loss=0.05,
                take_profit=0.10,
                reason="无相关事件"
            )

        # 分析每个事件
        signals = [self.analyze_event(e) for e in events]

        # 综合评分
        buy_score = sum(s.strength for s in signals if s.signal == 'buy')
        sell_score = sum(s.strength for s in signals if s.signal == 'sell')

        net_score = buy_score - sell_score

        if net_score > 0.5:
            signal = 'buy'
            strength = min(1.0, net_score)
        elif net_score < -0.5:
            signal = 'sell'
            strength = min(1.0, abs(net_score))
        else:
            signal = 'hold'
            strength = 0.3

        # 找到最重要的事件
        main_event = max(events, key=lambda e: abs(e.impact_score) * e.confidence)

        reasons = [s.reason for s in signals if s.signal != 'hold']

        return EventSignal(
            symbol=symbol,
            event=main_event,
            signal=signal,
            strength=strength,
            entry_window=min(s.entry_window for s in signals),
            holding_period=max(s.holding_period for s in signals),
            stop_loss=min(s.stop_loss for s in signals),
            take_profit=max(s.take_profit for s in signals),
            reason="; ".join(reasons[:3]) if reasons else "综合多事件分析"
        )


# 便捷函数
def create_earnings_event(symbol: str, date: datetime,
                         eps_actual: float, eps_estimate: float,
                         revenue_growth: float = 0,
                         profit_growth: float = 0) -> Event:
    """创建财报事件"""
    eps_surprise = (eps_actual - eps_estimate) / abs(eps_estimate) * 100 if eps_estimate else 0

    impact = 0
    if eps_surprise > 10:
        impact = 0.5
    elif eps_surprise > 5:
        impact = 0.3
    elif eps_surprise < -10:
        impact = -0.5
    elif eps_surprise < -5:
        impact = -0.3

    return Event(
        event_type=EventType.EARNINGS,
        symbol=symbol,
        date=date,
        title=f"财报发布: EPS {eps_actual:.2f} (预期 {eps_estimate:.2f})",
        content=f"EPS超预期{eps_surprise:.1f}%, 营收增长{revenue_growth:.1f}%, 净利增长{profit_growth:.1f}%",
        impact_score=impact,
        confidence=0.8,
        data={
            'eps_actual': eps_actual,
            'eps_estimate': eps_estimate,
            'revenue_growth': revenue_growth,
            'profit_growth': profit_growth
        }
    )


def create_holder_change_event(symbol: str, date: datetime,
                              holder_type: str, change_type: str,
                              change_ratio: float, holder_name: str = "") -> Event:
    """创建增减持事件"""
    impact = change_ratio / 10 if change_type == 'increase' else -change_ratio / 10
    impact = max(-1, min(1, impact))

    change_str = "增持" if change_type == 'increase' else "减持"
    type_str = {'major': '大股东', 'executive': '高管', 'fund': '基金'}.get(holder_type, '股东')

    return Event(
        event_type=EventType.HOLDER_CHANGE,
        symbol=symbol,
        date=date,
        title=f"{type_str}{change_str}{change_ratio:.2f}%",
        content=f"{holder_name or type_str}{change_str}{change_ratio:.2f}%股份",
        impact_score=impact,
        confidence=0.9,
        data={
            'holder_type': holder_type,
            'change_type': change_type,
            'change_ratio': change_ratio,
            'holder_name': holder_name
        }
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("事件驱动策略测试")
    print("=" * 60)

    strategy = EventDrivenStrategy()

    # 测试财报事件
    earnings_event = create_earnings_event(
        symbol="600519",
        date=datetime.now(),
        eps_actual=2.5,
        eps_estimate=2.2,
        revenue_growth=15.0,
        profit_growth=20.0
    )

    print("\n【财报事件分析】")
    signal = strategy.analyze_event(earnings_event)
    print(f"事件: {earnings_event.title}")
    print(f"信号: {signal.signal}")
    print(f"强度: {signal.strength:.2f}")
    print(f"原因: {signal.reason}")

    # 测试增减持事件
    holder_event = create_holder_change_event(
        symbol="000001",
        date=datetime.now(),
        holder_type="major",
        change_type="increase",
        change_ratio=3.5,
        holder_name="控股股东"
    )

    print("\n【增减持事件分析】")
    signal = strategy.analyze_event(holder_event)
    print(f"事件: {holder_event.title}")
    print(f"信号: {signal.signal}")
    print(f"强度: {signal.strength:.2f}")
    print(f"原因: {signal.reason}")

    print("\n" + "=" * 60)
