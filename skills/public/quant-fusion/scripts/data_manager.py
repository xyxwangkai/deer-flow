#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管理模块
基于Qlib的数据处理框架，提供统一的数据接口
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import json
import pickle
import os

logger = logging.getLogger(__name__)


class DataManager:
    """数据管理器 - Qlib风格的数据处理"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据管理器
        
        Args:
            config: 数据配置
        """
        self.config = config
        self.cache_dir = "data/cache"
        self.historical_data = {}
        self.real_time_data = {}
        self.feature_store = {}
        
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化数据源
        self.data_sources = self._init_data_sources()
        
        logger.info("数据管理器初始化完成")
    
    def _init_data_sources(self) -> Dict[str, Any]:
        """初始化数据源"""
        sources = {}
        
        # 股票数据源
        stock_config = self.config.get("stock_data", {})
        provider = stock_config.get("provider", "akshare")
        
        if provider == "akshare":
            from data_providers.akshare_provider import AkshareProvider
            sources["stock"] = AkshareProvider(stock_config)
        elif provider == "tushare":
            from data_providers.tushare_provider import TushareProvider
            sources["stock"] = TushareProvider(stock_config)
        else:
            # 使用模拟数据源
            from data_providers.mock_provider import MockProvider
            sources["stock"] = MockProvider(stock_config)
        
        # 市场数据源
        market_config = self.config.get("market_data", {})
        if market_config.get("real_time", False):
            from data_providers.market_provider import MarketProvider
            sources["market"] = MarketProvider(market_config)
        
        # 新闻数据源
        if self.config.get("news_data", {}).get("enabled", False):
            from data_providers.news_provider import NewsProvider
            sources["news"] = NewsProvider(self.config["news_data"])
        
        return sources
    
    async def get_stock_history(self, symbol: str, 
                              start_date: str, 
                              end_date: str,
                              fields: List[str] = None) -> pd.DataFrame:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            fields: 需要获取的字段列表
            
        Returns:
            pandas DataFrame
        """
        cache_key = f"{symbol}_{start_date}_{end_date}"
        
        # 检查缓存
        if cache_key in self.historical_data:
            logger.debug(f"从缓存获取历史数据: {symbol}")
            return self.historical_data[cache_key]
        
        # 从数据源获取
        if "stock" not in self.data_sources:
            logger.error("股票数据源未配置")
            return pd.DataFrame()
        
        try:
            df = await self.data_sources["stock"].get_history(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                fields=fields
            )
            
            # 缓存数据
            self.historical_data[cache_key] = df
            
            # 保存到文件缓存
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
            df.to_pickle(cache_file)
            
            logger.info(f"获取历史数据成功: {symbol} ({len(df)} 条记录)")
            return df
            
        except Exception as e:
            logger.error(f"获取历史数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    async def get_real_time_quote(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """
        获取实时行情
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            实时行情字典
        """
        if "market" not in self.data_sources:
            logger.warning("实时市场数据源未配置，使用模拟数据")
            return self._get_mock_real_time_quotes(symbols)
        
        try:
            quotes = await self.data_sources["market"].get_real_time_quotes(symbols)
            return quotes
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return self._get_mock_real_time_quotes(symbols)
    
    def _get_mock_real_time_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """生成模拟实时行情"""
        quotes = {}
        for symbol in symbols:
            # 模拟价格波动
            base_price = 100 + (hash(symbol) % 50)
            change = np.random.normal(0, 2)  # 正态分布波动
            
            quotes[symbol] = {
                "price": max(0.01, base_price + change),
                "volume": np.random.randint(10000, 1000000),
                "change": change,
                "change_percent": change / base_price * 100,
                "timestamp": datetime.now().isoformat()
            }
        return quotes
    
    async def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            添加技术指标的DataFrame
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        # 移动平均线
        result_df['MA5'] = result_df['close'].rolling(window=5).mean()
        result_df['MA10'] = result_df['close'].rolling(window=10).mean()
        result_df['MA20'] = result_df['close'].rolling(window=20).mean()
        result_df['MA60'] = result_df['close'].rolling(window=60).mean()
        
        # 布林带
        result_df['BB_middle'] = result_df['close'].rolling(window=20).mean()
        bb_std = result_df['close'].rolling(window=20).std()
        result_df['BB_upper'] = result_df['BB_middle'] + 2 * bb_std
        result_df['BB_lower'] = result_df['BB_middle'] - 2 * bb_std
        
        # RSI
        delta = result_df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        result_df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = result_df['close'].ewm(span=12, adjust=False).mean()
        exp2 = result_df['close'].ewm(span=26, adjust=False).mean()
        result_df['MACD'] = exp1 - exp2
        result_df['MACD_signal'] = result_df['MACD'].ewm(span=9, adjust=False).mean()
        result_df['MACD_hist'] = result_df['MACD'] - result_df['MACD_signal']
        
        # 成交量指标
        result_df['Volume_MA5'] = result_df['volume'].rolling(window=5).mean()
        result_df['Volume_MA10'] = result_df['volume'].rolling(window=10).mean()
        
        # 波动率
        result_df['Volatility'] = result_df['close'].rolling(window=20).std() / result_df['close'].rolling(window=20).mean()
        
        logger.debug(f"计算技术指标完成，新增 {len(result_df.columns) - len(df.columns)} 个指标")
        return result_df
    
    async def extract_features(self, df: pd.DataFrame, feature_config: Dict[str, Any]) -> pd.DataFrame:
        """
        提取特征 (Qlib风格的特征工程)
        
        Args:
            df: 原始数据DataFrame
            feature_config: 特征配置
            
        Returns:
            包含特征的DataFrame
        """
        if df.empty:
            return df
        
        feature_df = df.copy()
        
        # 价格相关特征
        feature_config = feature_config or {}
        
        # 收益率特征
        feature_df['return_1d'] = feature_df['close'].pct_change(1)
        feature_df['return_5d'] = feature_df['close'].pct_change(5)
        feature_df['return_20d'] = feature_df['close'].pct_change(20)
        
        # 波动特征
        feature_df['volatility_5d'] = feature_df['return_1d'].rolling(5).std()
        feature_df['volatility_20d'] = feature_df['return_1d'].rolling(20).std()
        
        # 量价关系特征
        feature_df['volume_price_ratio'] = feature_df['volume'] / feature_df['close']
        feature_df['volume_change'] = feature_df['volume'].pct_change()
        
        # 技术指标特征
        feature_df = await self.calculate_technical_indicators(feature_df)
        
        # 时间特征
        if 'date' in feature_df.columns:
            feature_df['day_of_week'] = pd.to_datetime(feature_df['date']).dt.dayofweek
            feature_df['month'] = pd.to_datetime(feature_df['date']).dt.month
            feature_df['quarter'] = pd.to_datetime(feature_df['date']).dt.quarter
        
        # 滞后特征
        for lag in [1, 2, 3, 5, 10]:
            feature_df[f'close_lag_{lag}'] = feature_df['close'].shift(lag)
            feature_df[f'volume_lag_{lag}'] = feature_df['volume'].shift(lag)
        
        # 移动窗口统计特征
        windows = [5, 10, 20, 60]
        for window in windows:
            feature_df[f'close_mean_{window}'] = feature_df['close'].rolling(window).mean()
            feature_df[f'close_std_{window}'] = feature_df['close'].rolling(window).std()
            feature_df[f'volume_mean_{window}'] = feature_df['volume'].rolling(window).mean()
            feature_df[f'volume_std_{window}'] = feature_df['volume'].rolling(window).std()
        
        # 处理缺失值
        feature_df = feature_df.fillna(method='ffill').fillna(method='bfill')
        
        logger.info(f"特征提取完成，共 {len(feature_df.columns)} 个特征")
        return feature_df
    
    async def get_market_sentiment(self, symbols: List[str] = None) -> Dict[str, float]:
        """
        获取市场情绪指标
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            情绪指标字典
        """
        sentiment_scores = {}
        
        if "news" in self.data_sources:
            try:
                news_sentiment = await self.data_sources["news"].get_sentiment(symbols)
                sentiment_scores.update(news_sentiment)
            except Exception as e:
                logger.error(f"获取新闻情绪失败: {e}")
        
        # 添加技术情绪指标
        for symbol in (symbols or []):
            # 基于价格和成交量的简单情绪指标
            if symbol in self.real_time_data:
                data = self.real_time_data[symbol]
                price_change = data.get('change_percent', 0)
                volume_ratio = data.get('volume', 0) / data.get('avg_volume', 1)
                
                # 综合情绪分数 (-1 到 1)
                sentiment = np.tanh(price_change * 0.1 + np.log(volume_ratio) * 0.05)
                sentiment_scores[symbol] = float(sentiment)
        
        return sentiment_scores
    
    async def update_cache(self):
        """更新数据缓存"""
        logger.info("开始更新数据缓存...")
        
        # 更新历史数据缓存
        cache_files = os.listdir(self.cache_dir)
        for cache_file in cache_files:
            if cache_file.endswith('.pkl'):
                try:
                    file_path = os.path.join(self.cache_dir, cache_file)
                    # 检查文件是否过期 (超过7天)
                    file_mtime = os.path.getmtime(file_path)
                    if datetime.now().timestamp() - file_mtime > 7 * 24 * 3600:
                        os.remove(file_path)
                        logger.debug(f"删除过期缓存: {cache_file}")
                except Exception as e:
                    logger.error(f"处理缓存文件失败 {cache_file}: {e}")
        
        logger.info("数据缓存更新完成")
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        stats = {
            "historical_data_count": len(self.historical_data),
            "real_time_symbols": list(self.real_time_data.keys()),
            "cache_files": len(os.listdir(self.cache_dir)) if os.path.exists(self.cache_dir) else 0,
            "feature_store_size": len(self.feature_store),
            "last_update": datetime.now().isoformat()
        }
        return stats


class RDAAgent:
    """RD-Agent: 基于强化学习的自动化因子挖掘代理 (Qlib特色功能)"""
    
    def __init__(self, data_manager: DataManager, config: Dict[str, Any]):
        """
        初始化RD-Agent
        
        Args:
            data_manager: 数据管理器
            config: 配置参数
        """
        self.data_manager = data_manager
        self.config = config
        self.learned_factors = []
        self.performance_history = []
        
        # 强化学习参数
        self.learning_rate = config.get("learning_rate", 0.01)
        self.exploration_rate = config.get("exploration_rate", 0.1)
        self.discount_factor = config.get("discount_factor", 0.9)
        
        logger.info("RD-Agent 初始化完成")
    
    async def discover_factors(self, symbols: List[str], 
                             target_metric: str = "return_5d") -> List[Dict[str, Any]]:
        """
        发现新的有效因子
        
        Args:
            symbols: 股票代码列表
            target_metric: 目标预测指标
            
        Returns:
            发现的因子列表
        """
        logger.info(f"开始因子挖掘，目标指标: {target_metric}")
        
        discovered_factors = []
        
        for symbol in symbols:
            try:
                # 获取历史数据
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
                
                df = await self.data_manager.get_stock_history(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if df.empty:
                    continue
                
                # 提取特征
                feature_df = await self.data_manager.extract_features(df, {})
                
                # 因子发现算法
                factors = await self._run_factor_discovery(feature_df, target_metric)
                
                for factor in factors:
                    factor["symbol"] = symbol
                    factor["discovery_date"] = datetime.now().isoformat()
                    discovered_factors.append(factor)
                    
                    logger.debug(f"发现因子: {factor.get('name')} (IC: {factor.get('ic', 0):.3f})")
                
            except Exception as e:
                logger.error(f"因子挖掘失败 {symbol}: {e}")
        
        # 评估因子有效性
        evaluated_factors = await self._evaluate_factors(discovered_factors)
        
        # 保存有效因子
        self.learned_factors.extend(evaluated_factors)
        
        logger.info(f"因子挖掘完成，发现 {len(evaluated_factors)} 个有效因子")
        return evaluated_factors
    
    async def _run_factor_discovery(self, feature_df: pd.DataFrame, 
                                  target_metric: str) -> List[Dict[str, Any]]:
        """运行因子发现算法"""
        factors = []
        
        if feature_df.empty or target_metric not in feature_df.columns:
            return factors
        
        # 计算每个特征与目标的相关性
        features = [col for col in feature_df.columns 
                   if col not in ['date', 'symbol', target_metric]]
        
        for feature in features:
            try:
                # 计算信息系数 (IC)
                ic = self._calculate_information_coefficient(
                    feature_df[feature], 
                    feature_df[target_metric]
                )
                
                # 计算因子收益
                factor_return = self._calculate_factor_return(
                    feature_df[feature], 
                    feature_df[target_metric]
                )
                
                # 计算稳定性
                stability = self._calculate_factor_stability(feature_df[feature])
                
                if abs(ic) > 0.05:  # IC绝对值大于0.05认为有效
                    factor = {
                        "name": feature,
                        "ic": float(ic),
                        "factor_return": float(factor_return),
                        "stability": float(stability),
                        "description": f"特征: {feature}",
                        "formula": f"df['{feature}']"
                    }
                    factors.append(factor)
                    
            except Exception as e:
                logger.debug(f"计算特征 {feature} 失败: {e}")
        
        # 按IC绝对值排序
        factors.sort(key=lambda x: abs(x["ic"]), reverse=True)
        
        return factors[:10]  # 返回前10个最有效的因子
    
    def _calculate_information_coefficient(self, feature: pd.Series, 
                                         target: pd.Series) -> float:
        """计算信息系数"""
        # 移除缺失值
        valid_mask = feature.notna() & target.notna()
        if valid_mask.sum() < 10:
            return 0.0
        
        # 计算相关系数
        try:
            from scipy.stats import spearmanr
            correlation, _ = spearmanr(
                feature[valid_mask].values,
                target[valid_mask].values
            )
            return correlation if not np.isnan(correlation) else 0.0
        except ImportError:
            # 如果没有scipy，使用pandas计算
            correlation = feature[valid_mask].corr(target[valid_mask], method='spearman')
            return correlation if not np.isnan(correlation) else 0.0
            return 0.0