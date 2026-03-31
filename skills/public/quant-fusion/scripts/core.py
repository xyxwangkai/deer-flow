#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化融合系统核心模块
融合Qlib、AlphaCouncil、TradingAgents三大项目的核心功能
"""

import os
import sys
import json
import yaml
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import pandas as pd
import numpy as np

# 导入AlphaCouncil相关类
from agents.council import AlphaCouncilAgent, AgentRole
# 导入DataManager
from data_manager import DataManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarketType(Enum):
    """市场类型枚举"""
    A_SHARE = "A股"
    US_STOCK = "美股"
    HK_STOCK = "港股"
    CRYPTO = "加密货币"
    FUTURES = "期货"


class AnalysisType(Enum):
    """分析类型枚举"""
    FUNDAMENTAL = "基本面分析"
    TECHNICAL = "技术面分析"
    SENTIMENT = "情绪面分析"
    CAPITAL_FLOW = "资金面分析"
    MACRO = "宏观面分析"
    RISK = "风险分析"


@dataclass
class StockData:
    """股票数据类"""
    symbol: str
    name: str
    market: MarketType
    price: float
    volume: int
    timestamp: datetime
    indicators: Dict[str, float] = field(default_factory=dict)
    fundamentals: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """分析结果类"""
    analyst_id: str
    analysis_type: AnalysisType
    symbol: str
    score: float  # 0-100分
    confidence: float  # 0-1置信度
    insights: List[str]
    recommendations: List[str]
    risks: List[str]
    timestamp: datetime


@dataclass
class TradingSignal:
    """交易信号类"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    price: float
    quantity: int
    reason: str
    confidence: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    expiry: Optional[datetime] = None


class QuantFusionSystem:
    """量化融合系统主类"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化量化融合系统
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.data_service = None
        self.analysts = []
        self.managers = []
        self.traders = []
        self.risk_managers = []
        self.is_initialized = False
        
        # 初始化组件
        self._init_components()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"配置文件加载成功: {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "data_sources": {
                "stock_data": {
                    "provider": "akshare",
                    "api_key": "",
                    "update_frequency": "1m"
                },
                "market_data": {
                    "real_time": True,
                    "sources": ["东方财富", "新浪财经"]
                }
            },
            "models": {
                "llm_providers": {
                    "openai": {"enabled": False},
                    "gemini": {"enabled": False},
                    "deepseek": {"enabled": True}
                }
            },
            "trading": {
                "broker": {
                    "type": "simulation",
                    "commission": 0.0003
                },
                "risk_management": {
                    "max_position_size": 0.1,
                    "max_daily_loss": 0.05,
                    "stop_loss": 0.03
                }
            },
            "agents": {
                "analysts_count": 5,
                "enable_parallel_analysis": True,
                "decision_threshold": 0.7
            }
        }
    
    def _init_components(self):
        """初始化系统组件"""
        logger.info("初始化系统组件...")
        
        # 初始化数据管理器 (Qlib风格的真实数据源)
        self.data_manager = DataManager(self.config["data_sources"])
        
        # 初始化分析师团队 (AlphaCouncil风格)
        self._init_analyst_team()
        
        # 初始化管理团队
        self._init_management_team()
        
        # 初始化交易团队 (TradingAgents风格)
        self._init_trading_team()
        
        self.is_initialized = True
        logger.info("系统组件初始化完成")
    
    async def _convert_to_stock_data(self, symbol: str, 
                                   real_time_quote: Dict[str, float],
                                   historical_data: pd.DataFrame = None) -> StockData:
        """
        将DataManager的数据转换为StockData格式
        
        Args:
            symbol: 股票代码
            real_time_quote: 实时行情数据
            historical_data: 历史数据DataFrame
            
        Returns:
            StockData对象
        """
        try:
            # 从实时行情获取基本信息
            price = real_time_quote.get("price", 0.0)
            volume = int(real_time_quote.get("volume", 0))
            timestamp = datetime.now()
            
            # 解析股票代码获取市场类型
            market = MarketType.A_SHARE  # 默认A股
            if symbol.endswith(".US"):
                market = MarketType.US_STOCK
            elif symbol.endswith(".HK"):
                market = MarketType.HK_STOCK
            
            # 创建StockData对象
            stock_data = StockData(
                symbol=symbol,
                name=f"股票{symbol}",
                market=market,
                price=price,
                volume=volume,
                timestamp=timestamp
            )
            
            # 从历史数据计算技术指标
            if historical_data is not None and not historical_data.empty:
                # 计算技术指标
                indicators = {}
                
                # 移动平均线
                if 'close' in historical_data.columns:
                    close_series = historical_data['close']
                    indicators['ma5'] = float(close_series.tail(5).mean()) if len(close_series) >= 5 else price
                    indicators['ma20'] = float(close_series.tail(20).mean()) if len(close_series) >= 20 else price
                    indicators['ma60'] = float(close_series.tail(60).mean()) if len(close_series) >= 60 else price
                
                # RSI (简化计算)
                if len(historical_data) >= 14 and 'close' in historical_data.columns:
                    close_changes = historical_data['close'].diff()
                    gains = close_changes[close_changes > 0].tail(14).mean()
                    losses = -close_changes[close_changes < 0].tail(14).mean()
                    if losses != 0:
                        rs = gains / losses
                        indicators['rsi'] = float(100 - (100 / (1 + rs)))
                    else:
                        indicators['rsi'] = 100.0
                
                # MACD (简化计算)
                if len(historical_data) >= 26 and 'close' in historical_data.columns:
                    close_series = historical_data['close']
                    ema12 = close_series.ewm(span=12, adjust=False).mean().iloc[-1]
                    ema26 = close_series.ewm(span=26, adjust=False).mean().iloc[-1]
                    indicators['macd'] = float(ema12 - ema26)
                
                stock_data.indicators = indicators
            
            # 添加模拟基本面数据（实际项目中应该从DataManager获取）
            stock_data.fundamentals = {
                "pe_ratio": 15.0 + (hash(symbol) % 20),
                "pb_ratio": 2.0 + (hash(symbol) % 3) / 10,
                "roe": 0.1 + (hash(symbol) % 15) / 100,
                "dividend_yield": 0.02 + (hash(symbol) % 5) / 1000,
                "market_cap": 1000000000 * (1 + (hash(symbol) % 100))
            }
            
            return stock_data
            
        except Exception as e:
            logger.error(f"转换股票数据失败 {symbol}: {e}")
            return None
    
    def _init_analyst_team(self):
        """初始化分析师团队"""
        # 映射AnalysisType到AgentRole
        analysis_to_role = {
            AnalysisType.FUNDAMENTAL: AgentRole.ANALYST_FUNDAMENTAL,
            AnalysisType.TECHNICAL: AgentRole.ANALYST_TECHNICAL,
            AnalysisType.SENTIMENT: AgentRole.ANALYST_SENTIMENT,
            AnalysisType.CAPITAL_FLOW: AgentRole.ANALYST_CAPITAL,
            AnalysisType.MACRO: AgentRole.ANALYST_MACRO,
            AnalysisType.RISK: AgentRole.ANALYST_RISK
        }
        
        analyst_configs = [
            {"id": "analyst_1", "type": AnalysisType.FUNDAMENTAL, "name": "基本面分析师"},
            {"id": "analyst_2", "type": AnalysisType.TECHNICAL, "name": "技术面分析师"},
            {"id": "analyst_3", "type": AnalysisType.SENTIMENT, "name": "情绪面分析师"},
            {"id": "analyst_4", "type": AnalysisType.CAPITAL_FLOW, "name": "资金面分析师"},
            {"id": "analyst_5", "type": AnalysisType.MACRO, "name": "宏观面分析师"}
        ]
        
        for config in analyst_configs:
            role = analysis_to_role.get(config["type"], AgentRole.ANALYST_FUNDAMENTAL)
            analyst_config = {
                "expertise": [config["name"]],
                "initial_confidence": 0.7,
                "personality": {"risk_tolerance": 0.5, "aggressiveness": 0.5}
            }
            
            analyst = AlphaCouncilAgent(
                agent_id=config["id"],
                role=role,
                config=analyst_config
            )
            self.analysts.append(analyst)
            logger.info(f"创建分析师: {config['name']} ({role.value})")
    
    def _init_management_team(self):
        """初始化管理团队"""
        # 总监 - 整合分析
        integration_director_config = {
            "expertise": ["整合分析", "共识构建", "冲突解决"],
            "initial_confidence": 0.8,
            "personality": {"risk_tolerance": 0.4, "aggressiveness": 0.3}
        }
        
        integration_director = AlphaCouncilAgent(
            agent_id="director_integration",
            role=AgentRole.DIRECTOR_INTEGRATION,
            config=integration_director_config
        )
        
        # 风控总监
        risk_director_config = {
            "expertise": ["风险评估", "合规审查", "风险监督"],
            "initial_confidence": 0.7,
            "personality": {"risk_tolerance": 0.2, "aggressiveness": 0.1}
        }
        
        risk_director = AlphaCouncilAgent(
            agent_id="director_risk",
            role=AgentRole.DIRECTOR_RISK,
            config=risk_director_config
        )
        
        # 总经理
        general_manager_config = {
            "expertise": ["战略决策", "资源配置", "绩效监督"],
            "initial_confidence": 0.9,
            "personality": {"risk_tolerance": 0.6, "aggressiveness": 0.4}
        }
        
        general_manager = AlphaCouncilAgent(
            agent_id="manager_general",
            role=AgentRole.MANAGER_GENERAL,
            config=general_manager_config
        )
        
        self.managers = [integration_director, risk_director, general_manager]
        logger.info("管理团队初始化完成")
    
    def _init_trading_team(self):
        """初始化交易团队"""
        # 交易员
        trader_config = {
            "expertise": ["订单执行", "做市", "算法交易"],
            "initial_confidence": 0.8,
            "personality": {"risk_tolerance": 0.3, "aggressiveness": 0.7}
        }
        
        trader = AlphaCouncilAgent(
            agent_id="trader_1",
            role=AgentRole.TRADER_EXECUTION,
            config=trader_config
        )
        
        # 风险经理 - 使用现有的RiskManager类
        risk_manager_config = {
            "expertise": ["风险评估", "风险监督", "合规检查"],
            "initial_confidence": 0.7,
            "personality": {"risk_tolerance": 0.1, "aggressiveness": 0.1}
        }
        
        risk_manager = AlphaCouncilAgent(
            agent_id="risk_manager_1",
            role=AgentRole.DIRECTOR_RISK,  # 使用风控总监角色
            config=risk_manager_config
        )
        
        # 研究员
        researcher_config = {
            "expertise": ["模型开发", "回测", "优化"],
            "initial_confidence": 0.6,
            "personality": {"risk_tolerance": 0.5, "aggressiveness": 0.2}
        }
        
        researcher = AlphaCouncilAgent(
            agent_id="researcher_1",
            role=AgentRole.RESEARCHER_QUANT,
            config=researcher_config
        )
        
        self.traders = [trader]
        self.risk_managers = [risk_manager]
        self.researchers = [researcher]
        logger.info("交易团队初始化完成")
    
    async def run_full_analysis(self, analysis_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行完整分析流程
        
        Args:
            analysis_config: 分析配置
            
        Returns:
            分析结果字典
        """
        logger.info("开始完整分析流程")
        
        # 1. 数据准备
        stock_data = await self._prepare_data(analysis_config)
        
        # 2. 并行分析 (AlphaCouncil风格)
        analysis_results = await self._run_parallel_analysis(stock_data)
        
        # 3. 整合报告
        integrated_report = await self._integrate_analysis(analysis_results)
        
        # 4. 风险评估
        risk_assessment = await self._assess_risks(integrated_report)
        
        # 5. 最终决策
        final_decision = await self._make_final_decision(
            integrated_report, 
            risk_assessment
        )
        
        # 6. 生成交易信号
        trading_signals = await self._generate_trading_signals(final_decision)
        
        return {
            "stock_data": stock_data,
            "analysis_results": analysis_results,
            "integrated_report": integrated_report,
            "risk_assessment": risk_assessment,
            "final_decision": final_decision,
            "trading_signals": trading_signals,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _prepare_data(self, config: Dict[str, Any]) -> List[StockData]:
        """准备数据 - 使用DataManager获取真实数据"""
        logger.info("准备市场数据...")
        
        symbols = config.get("symbols", [])
        timeframe = config.get("timeframe", "1d")
        start_date = config.get("start_date")
        end_date = config.get("end_date", datetime.now())
        
        if not symbols:
            logger.warning("没有指定股票代码")
            return []
        
        # 获取实时行情
        try:
            real_time_quotes = await self.data_manager.get_real_time_quote(symbols)
            logger.info(f"获取实时行情成功，共 {len(real_time_quotes)} 只股票")
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return []
        
        # 获取历史数据并转换为StockData格式
        stock_data_list = []
        start_date_str = start_date.strftime("%Y-%m-%d") if start_date else (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d") if isinstance(end_date, datetime) else datetime.now().strftime("%Y-%m-%d")
        
        for symbol in symbols:
            try:
                if symbol not in real_time_quotes:
                    logger.warning(f"股票 {symbol} 没有实时行情数据")
                    continue
                
                # 获取历史数据
                historical_data = await self.data_manager.get_stock_history(
                    symbol=symbol,
                    start_date=start_date_str,
                    end_date=end_date_str
                )
                
                # 转换为StockData格式
                stock_data = await self._convert_to_stock_data(
                    symbol=symbol,
                    real_time_quote=real_time_quotes[symbol],
                    historical_data=historical_data
                )
                
                if stock_data is not None:
                    stock_data_list.append(stock_data)
                    logger.info(f"准备数据成功: {symbol}")
                else:
                    logger.warning(f"转换股票数据失败: {symbol}")
                    
            except Exception as e:
                logger.error(f"处理股票数据失败 {symbol}: {e}")
        
        logger.info(f"数据准备完成，共 {len(stock_data_list)} 只股票")
        return stock_data_list
    
    async def _run_parallel_analysis(self, stock_data: List[StockData]) -> Dict[str, List[AnalysisResult]]:
        """并行分析"""
        logger.info("开始并行分析...")
        
        # 验证输入数据
        valid_stock_data = [stock for stock in stock_data if stock is not None]
        if not valid_stock_data:
            logger.error("没有有效的股票数据进行分析")
            return {}
        
        analysis_tasks = []
        for analyst in self.analysts:
            for stock in valid_stock_data:
                # 准备分析上下文
                context = {
                    "symbol": stock.symbol,
                    "timestamp": datetime.now(),
                    "market_condition": "NORMAL",
                    "data_type": "stock"
                }
                task = analyst.analyze(stock, context)
                analysis_tasks.append(task)
        
        # 等待所有分析完成
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # 整理结果
        organized_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"分析任务失败: {result}")
                continue
            
            if result is None:
                logger.warning(f"分析任务返回None")
                continue
            
            # 获取对应的股票
            stock_idx = i // len(self.analysts)
            if stock_idx < len(valid_stock_data):
                symbol = valid_stock_data[stock_idx].symbol
                if symbol not in organized_results:
                    organized_results[symbol] = []
                organized_results[symbol].append(result)
        
        logger.info(f"并行分析完成，共分析 {len(valid_stock_data)} 只股票")
        return organized_results
    
    async def _integrate_analysis(self, analysis_results: Dict[str, List[AnalysisResult]]) -> Dict[str, Any]:
        """整合分析报告"""
        logger.info("整合分析报告...")
        
        integration_director = next(
            (m for m in self.managers if m.agent_id == "director_integration"), 
            None
        )
        
        if not integration_director:
            logger.error("整合总监未找到")
            return {}
        
        integrated_report = await integration_director.integrate_reports(analysis_results)
        return integrated_report
    
    async def _assess_risks(self, integrated_report: Dict[str, Any]) -> Dict[str, Any]:
        """风险评估"""
        logger.info("进行风险评估...")
        
        risk_director = next(
            (m for m in self.managers if m.agent_id == "director_risk"), 
            None
        )
        
        if not risk_director:
            logger.error("风控总监未找到")
            return {}
        
        risk_assessment = await risk_director.assess_risks(integrated_report)
        return risk_assessment
    
    async def _make_final_decision(self, integrated_report: Dict[str, Any], 
                                 risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """最终决策"""
        logger.info("进行最终决策...")
        
        general_manager = next(
            (m for m in self.managers if m.agent_id == "manager_general"), 
            None
        )
        
        if not general_manager:
            logger.error("总经理未找到")
            return {}
        
        final_decision = await general_manager.make_decision(
            integrated_report, 
            risk_assessment
        )
        return final_decision
    
    async def _generate_trading_signals(self, final_decision: Dict[str, Any]) -> List[TradingSignal]:
        """生成交易信号"""
        logger.info("生成交易信号...")
        
        signals = []
        
        if "recommendations" not in final_decision:
            logger.warning("最终决策中没有推荐信息")
            return signals
        
        for recommendation in final_decision["recommendations"]:
            try:
                signal = TradingSignal(
                    symbol=recommendation.get("symbol"),
                    action=recommendation.get("action", "HOLD"),
                    price=recommendation.get("price", 0),
                    quantity=recommendation.get("quantity", 0),
                    reason=recommendation.get("reason", ""),
                    confidence=recommendation.get("confidence", 0.5),
                    stop_loss=recommendation.get("stop_loss"),
                    take_profit=recommendation.get("take_profit")
                )
                signals.append(signal)
            except Exception as e:
                logger.error(f"生成交易信号失败: {e}")
        
        logger.info(f"生成 {len(signals)} 个交易信号")
        return signals
    
    async def execute_trades(self, signals: List[TradingSignal], 
                           capital: float = 100000) -> Dict[str, Any]:
        """
        执行交易
        
        Args:
            signals: 交易信号列表
            capital: 初始资金
            
        Returns:
            交易执行结果
        """
        logger.info(f"开始执行交易，初始资金: {capital}")
        
        if not signals:
            logger.warning("没有交易信号可执行")
            return {"error": "没有交易信号"}
        
        execution_results = {
            "initial_capital": capital,
            "trades": [],
            "current_capital": capital,
            "positions": [],
            "performance": {}
        }
        
        # 风险检查
        risk_manager = self.risk_managers[0] if self.risk_managers else None
        if risk_manager:
            approved_signals = await risk_manager.approve_trades(signals, capital)
        else:
            approved_signals = signals
        
        # 执行交易
        trader = self.traders[0] if self.traders else None
        if not trader:
            logger.error("交易员未找到")
            return {"error": "交易员未找到"}
        
        for signal in approved_signals:
            try:
                trade_result = await trader.execute_trade(signal, capital)
                execution_results["trades"].append(trade_result)
                
                # 更新资金和仓位
                if trade_result.get("success"):
                    capital -= trade_result.get("cost", 0)
                    execution_results["current_capital"] = capital
                    
                    position = {
                        "symbol": signal.symbol,
                        "quantity": signal.quantity,
                        "entry_price": signal.price,
                        "current_price": signal.price,
                        "pnl": 0
                    }
                    execution_results["positions"].append(position)
                    
            except Exception as e:
                logger.error(f"执行交易失败 {signal.symbol}: {e}")
                execution_results["trades"].append({
                    "symbol": signal.symbol,
                    "success": False,
                    "error": str(e)
                })
        
        # 计算绩效
        execution_results["performance"] = await self._calculate_performance(
            execution_results["trades"],
            execution_results["positions"],
            execution_results["initial_capital"]
        )
        
        logger.info(f"交易执行完成，当前资金: {execution_results['current_capital']}")
        return execution_results
    
    async def _calculate_performance(self, trades: List[Dict], positions: List[Dict], 
                                   initial_capital: float) -> Dict[str, float]:
        """计算绩效指标"""
        if not trades:
            return {}
        
        total_trades = len(trades)
        successful_trades = len([t for t in trades if t.get("success")])
        success_rate = successful_trades / total_trades if total_trades > 0 else 0
        
        total_pnl = sum(p.get("pnl", 0) for p in positions)
        total_return = total_pnl / initial_capital if initial_capital > 0 else 0
        
        return {
            "total_trades": total_trades,
            "successful_trades": successful_trades,
            "success_rate": success_rate,
            "total_pnl": total_pnl,
            "total_return": total_return,
            "sharpe_ratio": 0,  # 需要更多数据计算
            "max_drawdown": 0   # 需要更多数据计算
        }


class DataService:
    """数据服务类 (Qlib风格)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = {}
        logger.info("数据服务初始化")
    
    async def get_stock_data(self, symbol: str, timeframe: str = "1d",
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> StockData:
        """获取股票数据"""
        # 这里应该实现实际的数据获取逻辑
        # 目前返回模拟数据
        
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        
        # 模拟数据
        stock_data = StockData(
            symbol=symbol,
            name=f"股票{symbol}",
            market=MarketType.A_SHARE,
            price=100.0 + (hash(symbol) % 100),
            volume=1000000 + (hash(symbol) % 9000000),
            timestamp=datetime.now()
        )
        
        # 添加模拟指标数据
        stock_data.indicators = {
            "ma5": 95.0 + (hash(symbol) % 50),
            "ma20": 90.0 + (hash(symbol) % 60),
            "rsi": 50.0 + (hash(symbol) % 30),
            "macd": (hash(symbol) % 20) - 10.0,
            "bollinger_upper": 110.0 + (hash(symbol) % 30),
            "bollinger_lower": 90.0 + (hash(symbol) % 20)
        }
        
        # 添加模拟基本面数据
        stock_data.fundamentals = {
            "pe_ratio": 15.0 + (hash(symbol) % 20),
            "pb_ratio": 2.0 + (hash(symbol) % 3) / 10,
            "roe": 0.1 + (hash(symbol) % 15) / 100,
            "dividend_yield": 0.02 + (hash(symbol) % 5) / 1000,
            "market_cap": 1000000000 * (1 + (hash(symbol) % 100))
        }
        
        return stock_data