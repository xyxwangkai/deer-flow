"""
模拟数据提供器 - 用于测试和开发环境
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np


class MockProvider:
    """模拟数据提供器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化模拟数据提供器
        
        Args:
            config: 配置参数
        """
        self.config = config
        self.stock_pool = config.get("stock_pool", ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"])
        self.base_prices = {
            "AAPL": 180.0,
            "GOOGL": 150.0,
            "MSFT": 400.0,
            "AMZN": 180.0,
            "TSLA": 200.0
        }
        
    async def get_stock_history(self, symbol: str, 
                              start_date: str, 
                              end_date: str,
                              frequency: str = "daily") -> pd.DataFrame:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            
        Returns:
            DataFrame包含历史数据
        """
        # 生成模拟数据
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        
        base_price = self.base_prices.get(symbol, 100.0)
        
        data = []
        price = base_price
        for date in dates:
            # 生成随机价格变动
            change_pct = random.uniform(-0.05, 0.05)
            price = price * (1 + change_pct)
            volume = random.randint(1000000, 10000000)
            
            data.append({
                "date": date,
                "open": price * (1 + random.uniform(-0.01, 0.01)),
                "high": price * (1 + random.uniform(0, 0.02)),
                "low": price * (1 + random.uniform(-0.02, 0)),
                "close": price,
                "volume": volume,
                "symbol": symbol
            })
        
        return pd.DataFrame(data)
    
    async def get_stock_realtime(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """
        获取股票实时数据
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            实时数据字典
        """
        result = {}
        for symbol in symbols:
            base_price = self.base_prices.get(symbol, 100.0)
            change_pct = random.uniform(-0.02, 0.02)
            current_price = base_price * (1 + change_pct)
            
            result[symbol] = {
                "price": current_price,
                "change": change_pct * 100,
                "volume": random.randint(500000, 5000000),
                "timestamp": datetime.now().isoformat()
            }
        
        return result
    
    async def get_market_indices(self) -> Dict[str, float]:
        """
        获取市场指数数据
        
        Returns:
            市场指数字典
        """
        return {
            "SPX": 5000.0 + random.uniform(-50, 50),
            "DJIA": 38000.0 + random.uniform(-100, 100),
            "NASDAQ": 16000.0 + random.uniform(-30, 30),
            "VIX": 15.0 + random.uniform(-2, 2)
        }
    
    async def get_financial_statements(self, symbol: str, 
                                     period: str = "annual") -> Dict[str, Any]:
        """
        获取财务报表数据
        
        Args:
            symbol: 股票代码
            period: 期间（annual/quarterly）
            
        Returns:
            财务报表数据
        """
        return {
            "income_statement": {
                "revenue": random.uniform(1000000, 10000000),
                "net_income": random.uniform(100000, 1000000),
                "eps": random.uniform(1, 10)
            },
            "balance_sheet": {
                "total_assets": random.uniform(5000000, 50000000),
                "total_liabilities": random.uniform(2000000, 20000000),
                "equity": random.uniform(3000000, 30000000)
            },
            "cash_flow": {
                "operating_cash_flow": random.uniform(500000, 5000000),
                "investing_cash_flow": random.uniform(-1000000, 1000000),
                "financing_cash_flow": random.uniform(-500000, 500000)
            }
        }
    
    async def get_news_sentiment(self, symbol: str, 
                               days: int = 7) -> Dict[str, Any]:
        """
        获取新闻情绪数据
        
        Args:
            symbol: 股票代码
            days: 天数
            
        Returns:
            新闻情绪数据
        """
        return {
            "symbol": symbol,
            "sentiment_score": random.uniform(-1, 1),
            "news_count": random.randint(5, 50),
            "positive_ratio": random.uniform(0, 1),
            "negative_ratio": random.uniform(0, 1),
            "keywords": ["earnings", "growth", "innovation", "market", "technology"]
        }
    
    async def validate_connection(self) -> bool:
        """
        验证连接
        
        Returns:
            是否连接成功
        """
        return True