"""
DeepSeek API 客户端
"""

import os
from openai import OpenAI
from typing import List, Optional, Dict
import json


class DeepSeekClient:
    """DeepSeek API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_key: API 密钥，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        
        if not self.api_key:
            raise ValueError("未设置 DeepSeek API Key")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        
        self.model = "deepseek-chat"
    
    def chat(self, messages: List[Dict[str, str]], 
             temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        聊天补全
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            AI 回复内容
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"DeepSeek API 调用失败: {e}")
            return ""
    
    def analyze_text(self, text: str, task: str = "sentiment") -> dict:
        """
        文本分析
        
        Args:
            text: 输入文本
            task: 任务类型 'sentiment', 'summary', 'extraction'
        
        Returns:
            分析结果
        """
        prompts = {
            'sentiment': """分析以下文本的情感倾向，返回 JSON 格式：
{
  "sentiment": "positive/negative/neutral",
  "score": 0-1之间的分数,
  "keywords": ["关键词1", "关键词2"]
}

文本：""",
            'summary': "请简洁地总结以下文本的要点：\n\n",
            'extraction': "从以下文本中提取关键信息和数据：\n\n"
        }
        
        prompt = prompts.get(task, prompts['sentiment'])
        
        messages = [
            {"role": "system", "content": "你是一个专业的金融文本分析助手。"},
            {"role": "user", "content": prompt + text}
        ]
        
        response = self.chat(messages, temperature=0.3)
        
        # 尝试解析 JSON
        try:
            return json.loads(response)
        except:
            return {"raw_response": response}
    
    def detect_anomaly(self, data: List[float], context: str = "") -> dict:
        """
        异常检测
        
        Args:
            data: 数据序列
            context: 上下文描述
        
        Returns:
            异常检测结果
        """
        prompt = f"""
你是一个数据异常检测专家。请分析以下数据序列，识别异常值。

上下文：{context if context else "股票价格数据"}
数据：{data[:50]}  # 只显示前50个

请返回 JSON 格式：
{{
  "has_anomaly": true/false,
  "anomaly_indices": [异常值的索引],
  "confidence": 0-1之间的置信度,
  "explanation": "异常原因说明"
}}
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的量化分析师。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.3, max_tokens=1000)
        
        try:
            return json.loads(response)
        except:
            return {"raw_response": response}
    
    def suggest_fill_method(self, data: List[float], 
                           missing_indices: List[int]) -> str:
        """
        建议缺失值填充方法
        
        Args:
            data: 数据序列
            missing_indices: 缺失值索引
        
        Returns:
            填充方法建议
        """
        prompt = f"""
数据序列有 {len(missing_indices)} 个缺失值。
样本数据：{data[:20]}
缺失位置：{missing_indices[:10]}

请推荐最合适的填充方法（线性插值/前向填充/均值填充/时间序列模型）并简要说明原因。
"""
        
        messages = [
            {"role": "system", "content": "你是一个数据处理专家。"},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat(messages, temperature=0.5, max_tokens=500)

