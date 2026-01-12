"""
情感分析器
"""

from typing import List, Dict
from .deepseek_client import DeepSeekClient


class SentimentAnalyzer:
    """新闻情感分析器"""
    
    def __init__(self, api_key: str = None):
        self.client = DeepSeekClient(api_key)
    
    def analyze_news(self, news_list: List[Dict]) -> List[Dict]:
        """
        分析新闻列表的情感
        
        Args:
            news_list: 新闻列表 [{"title": "...", "content": "..."}]
        
        Returns:
            带情感分数的新闻列表
        """
        results = []
        
        for news in news_list:
            title = news.get('title', '')
            content = news.get('content', '')[:500]  # 限制长度
            
            text = f"标题：{title}\n内容：{content}"
            
            sentiment = self.client.analyze_text(text, task='sentiment')
            
            news_with_sentiment = news.copy()
            news_with_sentiment['sentiment'] = sentiment.get('sentiment', 'neutral')
            news_with_sentiment['sentiment_score'] = sentiment.get('score', 0.5)
            news_with_sentiment['keywords'] = sentiment.get('keywords', [])
            
            results.append(news_with_sentiment)
        
        return results
    
    def calculate_market_sentiment(self, news_list: List[Dict]) -> Dict:
        """
        计算整体市场情绪
        
        Args:
            news_list: 新闻列表
        
        Returns:
            市场情绪指标
        """
        analyzed = self.analyze_news(news_list)
        
        if not analyzed:
            return {
                'overall_sentiment': 'neutral',
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0,
                'avg_score': 0.5
            }
        
        sentiments = [n['sentiment'] for n in analyzed]
        scores = [n['sentiment_score'] for n in analyzed]
        
        total = len(sentiments)
        positive = sentiments.count('positive')
        negative = sentiments.count('negative')
        neutral = sentiments.count('neutral')
        
        avg_score = sum(scores) / len(scores)
        
        # 判断整体情绪
        if positive > negative and avg_score > 0.6:
            overall = 'positive'
        elif negative > positive and avg_score < 0.4:
            overall = 'negative'
        else:
            overall = 'neutral'
        
        return {
            'overall_sentiment': overall,
            'positive_ratio': positive / total,
            'negative_ratio': negative / total,
            'neutral_ratio': neutral / total,
            'avg_score': avg_score,
            'sample_size': total
        }

