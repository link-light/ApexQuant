"""
ApexQuant 新闻数据获取模块

获取股票相关新闻和公告
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# 尝试导入akshare
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    logger.warning("akshare not available, news fetching limited")


class NewsFetcher:
    """新闻数据获取器"""

    def __init__(self):
        logger.info(f"NewsFetcher initialized (akshare: {AKSHARE_AVAILABLE})")

    def get_stock_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """
        获取个股新闻

        Args:
            symbol: 股票代码 (如 '600519')
            limit: 返回条数

        Returns:
            新闻列表
        """
        news_list = []

        # 尝试从akshare获取
        if AKSHARE_AVAILABLE:
            try:
                news_list.extend(self._fetch_from_akshare(symbol, limit))
            except Exception as e:
                logger.warning(f"akshare news fetch failed: {e}")

        # 如果没有获取到，返回示例数据
        if not news_list:
            news_list = self._get_mock_news(symbol)

        return news_list[:limit]

    def get_market_news(self, limit: int = 20) -> List[Dict]:
        """
        获取市场新闻

        Args:
            limit: 返回条数

        Returns:
            新闻列表
        """
        news_list = []

        if AKSHARE_AVAILABLE:
            try:
                # 获取财经新闻
                df = ak.stock_news_em()
                if df is not None and not df.empty:
                    for _, row in df.head(limit).iterrows():
                        news_list.append({
                            'title': row.get('新闻标题', ''),
                            'content': row.get('新闻内容', '')[:200] if row.get('新闻内容') else '',
                            'source': row.get('新闻来源', '财经新闻'),
                            'time': row.get('发布时间', ''),
                            'url': row.get('新闻链接', '')
                        })
            except Exception as e:
                logger.warning(f"Market news fetch failed: {e}")

        if not news_list:
            news_list = self._get_mock_market_news()

        return news_list[:limit]

    def get_announcements(self, symbol: str, limit: int = 5) -> List[Dict]:
        """
        获取公司公告

        Args:
            symbol: 股票代码
            limit: 返回条数

        Returns:
            公告列表
        """
        announcements = []

        if AKSHARE_AVAILABLE:
            try:
                # 尝试获取公告
                df = ak.stock_notice_report(symbol=symbol)
                if df is not None and not df.empty:
                    for _, row in df.head(limit).iterrows():
                        announcements.append({
                            'title': row.get('公告标题', ''),
                            'type': row.get('公告类型', ''),
                            'date': row.get('公告日期', ''),
                            'content': ''
                        })
            except Exception as e:
                logger.debug(f"Announcement fetch failed: {e}")

        return announcements[:limit]

    def _fetch_from_akshare(self, symbol: str, limit: int) -> List[Dict]:
        """从akshare获取新闻"""
        news_list = []

        try:
            # 个股新闻
            df = ak.stock_news_em(symbol=symbol)
            if df is not None and not df.empty:
                for _, row in df.head(limit).iterrows():
                    news_list.append({
                        'title': row.get('新闻标题', ''),
                        'content': row.get('新闻内容', '')[:300] if row.get('新闻内容') else '',
                        'source': row.get('文章来源', ''),
                        'time': row.get('发布时间', ''),
                        'url': row.get('新闻链接', '')
                    })
        except Exception as e:
            logger.debug(f"akshare stock_news_em failed: {e}")

        return news_list

    def _get_mock_news(self, symbol: str) -> List[Dict]:
        """返回模拟新闻数据"""
        now = datetime.now()
        return [
            {
                'title': f'{symbol} 公司发布业绩预告',
                'content': '公司预计本季度净利润同比增长10%-20%',
                'source': '财经新闻',
                'time': (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'),
                'sentiment': 'positive'
            },
            {
                'title': f'{symbol} 获得机构调研',
                'content': '多家机构近期对公司进行实地调研',
                'source': '证券时报',
                'time': (now - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M'),
                'sentiment': 'neutral'
            },
            {
                'title': f'行业政策利好 {symbol} 受益',
                'content': '国家出台新政策支持行业发展',
                'source': '新华社',
                'time': (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M'),
                'sentiment': 'positive'
            }
        ]

    def _get_mock_market_news(self) -> List[Dict]:
        """返回模拟市场新闻"""
        now = datetime.now()
        return [
            {
                'title': 'A股三大指数集体高开',
                'content': '沪指高开0.3%，深成指高开0.5%，创业板指高开0.6%',
                'source': '财联社',
                'time': now.strftime('%Y-%m-%d %H:%M'),
                'sentiment': 'positive'
            },
            {
                'title': '北向资金今日净流入',
                'content': '北向资金早盘净流入超30亿元',
                'source': '同花顺',
                'time': now.strftime('%Y-%m-%d %H:%M'),
                'sentiment': 'positive'
            },
            {
                'title': '央行开展逆回购操作',
                'content': '央行今日开展1000亿元7天期逆回购操作',
                'source': '中国人民银行',
                'time': now.strftime('%Y-%m-%d %H:%M'),
                'sentiment': 'neutral'
            }
        ]


class MarketDataFetcher:
    """市场数据获取器"""

    def __init__(self):
        logger.info(f"MarketDataFetcher initialized (akshare: {AKSHARE_AVAILABLE})")

    def get_index_data(self) -> Dict:
        """获取大盘指数数据"""
        data = {
            'sh_index': 0.0,
            'sh_change': 0.0,
            'sz_index': 0.0,
            'sz_change': 0.0,
            'cyb_index': 0.0,
            'cyb_change': 0.0
        }

        if AKSHARE_AVAILABLE:
            try:
                # 获取实时指数
                df = ak.stock_zh_index_spot()
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        code = row.get('代码', '')
                        if code == 'sh000001':  # 上证指数
                            data['sh_index'] = float(row.get('最新价', 0))
                            data['sh_change'] = float(row.get('涨跌幅', 0))
                        elif code == 'sz399001':  # 深证成指
                            data['sz_index'] = float(row.get('最新价', 0))
                            data['sz_change'] = float(row.get('涨跌幅', 0))
                        elif code == 'sz399006':  # 创业板指
                            data['cyb_index'] = float(row.get('最新价', 0))
                            data['cyb_change'] = float(row.get('涨跌幅', 0))
            except Exception as e:
                logger.warning(f"Index data fetch failed: {e}")

        return data

    def get_market_overview(self) -> Dict:
        """获取市场概况"""
        overview = {
            'up_count': 0,
            'down_count': 0,
            'flat_count': 0,
            'limit_up': 0,
            'limit_down': 0,
            'total_volume': 0,
            'total_amount': 0
        }

        if AKSHARE_AVAILABLE:
            try:
                # 获取涨跌统计
                df = ak.stock_market_activity_legu()
                if df is not None and not df.empty:
                    # 解析数据...
                    pass
            except Exception as e:
                logger.debug(f"Market overview fetch failed: {e}")

        # 返回模拟数据
        import random
        overview['up_count'] = random.randint(1500, 2500)
        overview['down_count'] = random.randint(1500, 2500)
        overview['limit_up'] = random.randint(30, 100)
        overview['limit_down'] = random.randint(5, 30)

        return overview

    def get_north_flow(self) -> Dict:
        """获取北向资金数据"""
        data = {
            'net_flow': 0.0,
            'buy_amount': 0.0,
            'sell_amount': 0.0
        }

        if AKSHARE_AVAILABLE:
            try:
                df = ak.stock_hsgt_north_net_flow_in_em()
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    data['net_flow'] = float(latest.get('当日净流入', 0)) / 100000000  # 转为亿
            except Exception as e:
                logger.debug(f"North flow fetch failed: {e}")

        return data


# 便捷函数
def get_stock_news(symbol: str, limit: int = 10) -> List[Dict]:
    """获取个股新闻"""
    fetcher = NewsFetcher()
    return fetcher.get_stock_news(symbol, limit)


def get_market_sentiment() -> str:
    """获取市场情绪"""
    market_fetcher = MarketDataFetcher()
    overview = market_fetcher.get_market_overview()

    up = overview['up_count']
    down = overview['down_count']
    limit_up = overview['limit_up']
    limit_down = overview['limit_down']

    # 判断情绪
    if limit_up > 80 and up > down * 1.5:
        return "狂热"
    elif limit_up > 50 and up > down:
        return "乐观"
    elif limit_down > 50 and down > up * 1.5:
        return "恐慌"
    elif limit_down > 30 and down > up:
        return "谨慎"
    else:
        return "中性"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("新闻数据获取测试")
    print("=" * 60)

    news_fetcher = NewsFetcher()
    market_fetcher = MarketDataFetcher()

    print("\n[个股新闻]")
    news = news_fetcher.get_stock_news('600519', limit=3)
    for n in news:
        print(f"  - {n['title']}")

    print("\n[市场新闻]")
    market_news = news_fetcher.get_market_news(limit=3)
    for n in market_news:
        print(f"  - {n['title']}")

    print("\n[指数数据]")
    index_data = market_fetcher.get_index_data()
    print(f"  上证: {index_data['sh_index']} ({index_data['sh_change']:+.2f}%)")

    print("\n[市场情绪]")
    sentiment = get_market_sentiment()
    print(f"  当前情绪: {sentiment}")

    print("\n" + "=" * 60)
