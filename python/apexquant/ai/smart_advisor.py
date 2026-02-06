"""
ApexQuant 智能AI交易顾问

整合技术指标、基本面、新闻舆情的全方位AI分析
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# 导入依赖
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai library not available")

# 导入技术分析模块
try:
    from apexquant.analysis import TechnicalAnalyzer, TechnicalIndicators
except ImportError:
    from ..analysis import TechnicalAnalyzer, TechnicalIndicators


@dataclass
class MarketContext:
    """市场环境数据"""
    # 大盘指数
    index_sh: float = 0.0       # 上证指数
    index_sh_change: float = 0.0  # 涨跌幅
    index_sz: float = 0.0       # 深证成指
    index_sz_change: float = 0.0

    # 市场情绪
    up_count: int = 0           # 上涨家数
    down_count: int = 0         # 下跌家数
    limit_up_count: int = 0     # 涨停家数
    limit_down_count: int = 0   # 跌停家数

    # 资金流向
    north_flow: float = 0.0     # 北向资金净流入（亿）
    main_flow: float = 0.0      # 主力资金净流入（亿）

    # 市场温度
    market_sentiment: str = "中性"  # 恐慌/谨慎/中性/乐观/狂热

    def to_text(self) -> str:
        return f"""【大盘环境】
上证指数: {self.index_sh:.2f} ({self.index_sh_change:+.2f}%)
深证成指: {self.index_sz:.2f} ({self.index_sz_change:+.2f}%)

【市场情绪】
涨跌家数: {self.up_count}↑ / {self.down_count}↓
涨停/跌停: {self.limit_up_count}涨停 / {self.limit_down_count}跌停
市场情绪: {self.market_sentiment}

【资金流向】
北向资金: {self.north_flow:+.2f}亿
主力资金: {self.main_flow:+.2f}亿"""


@dataclass
class FundamentalData:
    """基本面数据"""
    pe_ratio: float = 0.0       # 市盈率
    pb_ratio: float = 0.0       # 市净率
    roe: float = 0.0            # ROE
    revenue_growth: float = 0.0  # 营收增长率
    profit_growth: float = 0.0   # 净利润增长率
    debt_ratio: float = 0.0      # 资产负债率
    market_cap: float = 0.0      # 总市值（亿）
    circulating_cap: float = 0.0 # 流通市值（亿）
    industry: str = ""           # 所属行业
    concept: str = ""            # 概念板块

    def to_text(self) -> str:
        return f"""【估值指标】
PE(TTM): {self.pe_ratio:.2f}
PB: {self.pb_ratio:.2f}
ROE: {self.roe:.2f}%

【成长指标】
营收增长: {self.revenue_growth:+.2f}%
净利增长: {self.profit_growth:+.2f}%

【规模指标】
总市值: {self.market_cap:.0f}亿
流通市值: {self.circulating_cap:.0f}亿
资产负债率: {self.debt_ratio:.1f}%

【分类】
行业: {self.industry}
概念: {self.concept}"""


@dataclass
class AIAnalysisResult:
    """AI分析结果"""
    action: str = "HOLD"            # BUY/SELL/HOLD
    confidence: float = 0.0         # 置信度 0-100
    position_advice: str = "观望"    # 建仓/加仓/减仓/清仓/观望
    position_ratio: float = 0.0     # 建议仓位比例 0-100%
    target_price: float = 0.0       # 目标价
    stop_loss: float = 0.0          # 止损价
    risk_level: str = "中等"         # 低/中等/高/极高
    time_horizon: str = "短期"       # 短期/中期/长期
    key_factors: List[str] = None   # 关键因素
    reasoning: str = ""             # 分析理由
    warnings: List[str] = None      # 风险提示

    def __post_init__(self):
        if self.key_factors is None:
            self.key_factors = []
        if self.warnings is None:
            self.warnings = []

    def to_dict(self) -> Dict:
        return asdict(self)


class SmartTradingAdvisor:
    """智能交易顾问"""

    SYSTEM_PROMPT = """你是ApexQuant量化交易系统的AI分析师，专注于A股市场分析。

你的任务是根据提供的数据进行全面分析，给出专业的交易建议。

分析维度：
1. 技术面：趋势、形态、指标信号
2. 基本面：估值、成长性、财务健康度
3. 资金面：主力动向、北向资金
4. 市场环境：大盘走势、板块轮动、市场情绪
5. 新闻舆情：利好利空消息

输出要求：
- 必须返回有效的JSON格式
- 分析要客观专业，不要过度乐观或悲观
- 给出明确的操作建议和风险提示
- 考虑A股T+1交易规则"""

    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        """
        初始化智能顾问

        Args:
            api_key: DeepSeek API密钥（可选，默认从环境变量读取）
            model: 模型名称
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("请安装openai库: pip install openai")

        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.model = model
        self.base_url = "https://api.deepseek.com"

        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=30
            )
            logger.info(f"SmartTradingAdvisor initialized with model: {self.model}")
        else:
            self.client = None
            logger.warning("API key not found, advisor disabled")

        # 技术分析器
        self.tech_analyzer = TechnicalAnalyzer()

        # 调用统计
        self.call_count = 0
        self.total_tokens = 0

    def analyze(
        self,
        symbol: str,
        price_data,  # DataFrame with OHLCV
        current_price: float,
        account_info: Dict,
        fundamental: FundamentalData = None,
        market_context: MarketContext = None,
        news: List[str] = None
    ) -> AIAnalysisResult:
        """
        全面分析股票

        Args:
            symbol: 股票代码
            price_data: 价格数据DataFrame
            current_price: 当前价格
            account_info: 账户信息
            fundamental: 基本面数据
            market_context: 市场环境
            news: 新闻列表

        Returns:
            AIAnalysisResult 分析结果
        """
        if not self.client:
            return AIAnalysisResult(
                action="HOLD",
                reasoning="AI服务未配置，请设置DEEPSEEK_API_KEY环境变量"
            )

        try:
            # 1. 计算技术指标
            tech_indicators = self.tech_analyzer.calculate(price_data, current_price)

            # 2. 构建分析prompt
            prompt = self._build_analysis_prompt(
                symbol=symbol,
                current_price=current_price,
                tech_indicators=tech_indicators,
                account_info=account_info,
                fundamental=fundamental,
                market_context=market_context,
                news=news
            )

            # 3. 调用AI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )

            # 4. 解析结果
            content = response.choices[0].message.content
            result = self._parse_response(content)

            # 统计
            self.call_count += 1
            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.total_tokens

            logger.info(f"AI分析完成: {symbol} -> {result.action} (置信度: {result.confidence}%)")

            return result

        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return AIAnalysisResult(
                action="HOLD",
                reasoning=f"分析出错: {str(e)}",
                warnings=["AI分析异常，建议人工判断"]
            )

    def _build_analysis_prompt(
        self,
        symbol: str,
        current_price: float,
        tech_indicators: TechnicalIndicators,
        account_info: Dict,
        fundamental: FundamentalData = None,
        market_context: MarketContext = None,
        news: List[str] = None
    ) -> str:
        """构建分析Prompt"""

        # 持仓信息
        positions = account_info.get('positions', [])
        position = next((p for p in positions if p.get('symbol') == symbol), None)

        if position:
            position_text = f"""【当前持仓】
持有数量: {position.get('volume', 0)}股
持仓成本: {position.get('avg_cost', 0):.2f}
浮动盈亏: {position.get('unrealized_pnl', 0):.2f}"""
        else:
            position_text = "【当前持仓】无"

        # 构建prompt
        prompt = f"""请分析以下股票并给出交易建议：

═══════════════════════════════════════
股票: {symbol}
当前价格: {current_price:.2f}
═══════════════════════════════════════

{tech_indicators.to_text()}

{position_text}

【账户状态】
总资产: {account_info.get('total_assets', 0):.0f}
可用资金: {account_info.get('available_cash', 0):.0f}
"""

        # 添加基本面数据
        if fundamental:
            prompt += f"\n{fundamental.to_text()}\n"

        # 添加市场环境
        if market_context:
            prompt += f"\n{market_context.to_text()}\n"

        # 添加新闻
        if news:
            prompt += "\n【近期新闻】\n"
            for i, n in enumerate(news[:5], 1):
                prompt += f"{i}. {n}\n"

        # 输出格式要求
        prompt += """
═══════════════════════════════════════
请返回JSON格式的分析结果（不要使用markdown）：
{
    "action": "BUY" 或 "SELL" 或 "HOLD",
    "confidence": 置信度(0-100),
    "position_advice": "建仓"/"加仓"/"减仓"/"清仓"/"观望",
    "position_ratio": 建议仓位比例(0-100),
    "target_price": 目标价,
    "stop_loss": 止损价,
    "risk_level": "低"/"中等"/"高"/"极高",
    "time_horizon": "短期"/"中期"/"长期",
    "key_factors": ["关键因素1", "关键因素2", ...],
    "reasoning": "详细分析理由(100-200字)",
    "warnings": ["风险提示1", "风险提示2", ...]
}
"""
        return prompt

    def _parse_response(self, text: str) -> AIAnalysisResult:
        """解析AI响应"""
        try:
            # 清理markdown标记
            text = text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()

            # 解析JSON
            data = json.loads(text)

            return AIAnalysisResult(
                action=data.get('action', 'HOLD').upper(),
                confidence=float(data.get('confidence', 0)),
                position_advice=data.get('position_advice', '观望'),
                position_ratio=float(data.get('position_ratio', 0)),
                target_price=float(data.get('target_price', 0)),
                stop_loss=float(data.get('stop_loss', 0)),
                risk_level=data.get('risk_level', '中等'),
                time_horizon=data.get('time_horizon', '短期'),
                key_factors=data.get('key_factors', []),
                reasoning=data.get('reasoning', ''),
                warnings=data.get('warnings', [])
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.debug(f"原始响应: {text}")
            return AIAnalysisResult(
                action="HOLD",
                reasoning="AI响应解析失败",
                warnings=["响应格式异常"]
            )

    def get_quick_signal(
        self,
        symbol: str,
        price_data,
        current_price: float
    ) -> Dict:
        """
        快速获取交易信号（仅技术面）

        Args:
            symbol: 股票代码
            price_data: 价格数据
            current_price: 当前价格

        Returns:
            简单信号字典
        """
        tech = self.tech_analyzer.calculate(price_data, current_price)

        # 基于指标的简单信号判断
        buy_signals = 0
        sell_signals = 0

        # RSI信号
        if tech.rsi < 30:
            buy_signals += 1
        elif tech.rsi > 70:
            sell_signals += 1

        # MACD信号
        if tech.macd > tech.macd_signal and tech.macd_hist > 0:
            buy_signals += 1
        elif tech.macd < tech.macd_signal and tech.macd_hist < 0:
            sell_signals += 1

        # KDJ信号
        if tech.kdj_signal == "金叉向上" or tech.kdj_signal == "超卖":
            buy_signals += 1
        elif tech.kdj_signal == "死叉向下" or tech.kdj_signal == "超买":
            sell_signals += 1

        # 趋势信号
        if tech.trend == "上涨":
            buy_signals += 1
        elif tech.trend == "下跌":
            sell_signals += 1

        # 布林带信号
        if tech.boll_position in ["跌破下轨", "下轨附近"]:
            buy_signals += 1
        elif tech.boll_position in ["突破上轨", "上轨附近"]:
            sell_signals += 1

        # 综合判断
        if buy_signals >= 3:
            action = "BUY"
            confidence = min(90, 50 + buy_signals * 10)
        elif sell_signals >= 3:
            action = "SELL"
            confidence = min(90, 50 + sell_signals * 10)
        else:
            action = "HOLD"
            confidence = 50

        return {
            'action': action,
            'confidence': confidence,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'indicators': tech.to_dict()
        }


# 测试代码
if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("SmartTradingAdvisor 测试")
    print("=" * 60)

    # 生成测试数据
    np.random.seed(42)
    dates = pd.date_range('2025-01-01', periods=60, freq='D')
    base_price = 100
    returns = np.random.randn(60) * 0.02
    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.randn(60) * 0.005),
        'high': prices * (1 + abs(np.random.randn(60) * 0.01)),
        'low': prices * (1 - abs(np.random.randn(60) * 0.01)),
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 60)
    })

    current_price = float(df['close'].iloc[-1])

    account_info = {
        'total_assets': 1000000,
        'available_cash': 500000,
        'positions': []
    }

    # 测试快速信号
    try:
        advisor = SmartTradingAdvisor()

        print("\n[快速信号测试]")
        signal = advisor.get_quick_signal('600519', df, current_price)
        print(f"信号: {signal['action']}")
        print(f"置信度: {signal['confidence']}%")
        print(f"买入信号数: {signal['buy_signals']}")
        print(f"卖出信号数: {signal['sell_signals']}")

        # 测试完整分析（需要API key）
        if advisor.client:
            print("\n[完整AI分析测试]")
            result = advisor.analyze(
                symbol='600519',
                price_data=df,
                current_price=current_price,
                account_info=account_info,
                news=["茅台发布年报，净利润增长15%", "白酒板块整体走强"]
            )
            print(f"建议: {result.action}")
            print(f"置信度: {result.confidence}%")
            print(f"仓位建议: {result.position_advice}")
            print(f"分析: {result.reasoning}")
        else:
            print("\n[跳过完整分析] API key未配置")

    except Exception as e:
        print(f"[ERROR] {e}")

    print("\n" + "=" * 60)
    print("测试完成!")
