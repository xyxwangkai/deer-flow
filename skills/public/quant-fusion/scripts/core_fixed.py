#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化融合系统 - 核心模块 (修复版)
修复了数据验证和None值处理问题
"""

import asyncio
import yaml
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# 导入其他模块
from data_manager import DataManager, RDAAgent
from trading_executor import TradingExecutor, Order, Position, Account, BrokerType
from risk_management import RiskManager, RiskMetrics, RiskLimit, RiskAlert
from agents.council import AlphaCouncilAgent, AgentRole, CouncilDecision


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
        
        # 初始化数据服务 (Qlib风格)
        self.data_service = DataService(self.config["data_sources"])
        
        # 初始化分析师团队 (AlphaCouncil风格)
        self._init_analyst_team()
        
        # 初始化管理团队
        self._init_management_team()
        
        # 初始化交易团队 (TradingAgents风格)
        self._init_trading_team()
        
        self.is_initialized = True
        logger.info("系统组件初始化完成")
    
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
            try:
                analyst = AlphaCouncilAgent(
                    agent_id=config["id"],
                    role=analysis_to_role[config["type"]],
                    name=config["name"]
                )
                self.analysts.append(analyst)
                logger.info(f"创建分析师: {config['name']} ({config['id']})")
            except Exception as e:
                logger.error(f"创建分析师失败 {config['id']}: {e}")
    
    def _init_management_team(self):
        """初始化管理团队"""
        manager_configs = [
            {"id": "director_integration", "role": AgentRole.DIRECTOR_INTEGRATION, "name": "整合总监"},
            {"id": "director_risk", "role": AgentRole.DIRECTOR_RISK, "name": "风控总监"},
            {"id": "manager_general", "role": AgentRole.MANAGER_GENERAL, "name": "总经理"}
        ]
        
        for config in manager_configs:
            try:
                manager = AlphaCouncilAgent(
                    agent_id=config["id"],
                    role=config["role"],
                    name=config["name"]
                )
                self.managers.append(manager)
                logger.info(f"创建管理者: {config['name']} ({config['id']})")
            except Exception as e:
                logger.error(f"创建管理者失败 {config['id']}: {e}")
    
    def _init_trading_team(self):
        """初始化交易团队"""
        trader_configs = [
            {"id": "trader_1", "role": AgentRole.TRADER, "name": "交易员"},
            {"id": "risk_manager_1", "role": AgentRole.RISK_MANAGER, "name": "风控总监"},
            {"id": "researcher_1", "role": AgentRole.RESEARCHER, "name": "量化研究员"}
        ]
        
        for config in trader_configs:
            try:
                trader = AlphaCouncilAgent(
                    agent_id=config["id"],
                    role=config["role"],
                    name=config["name"]
                )
                self.traders.append(trader)
                logger.info(f"创建交易员: {config['name']} ({config['id']})")
            except Exception as e:
                logger.error(f"创建交易员失败 {config['id']}: {e}")
    
    async def run_full_analysis(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行完整分析流程
        
        Args:
            config: 分析配置
            
        Returns:
            完整分析结果
        """
        if not self.is_initialized:
            self._init_components()
        
        logger.info("开始完整分析流程")
        
        # 1. 准备市场数据
        stock_data = await self._prepare_data(config)
        
        # 验证数据
        if not stock_data:
            logger.error("未获取到有效数据")
            return {"error": "未获取到有效数据"}
        
        # 2. 并行分析
        analysis_results = await self._run_parallel_analysis(stock_data)
        
        # 3. 整合分析报告
        integrated_report = await self._integrate_reports(analysis_results)
        
        # 4. 风险评估
        risk_assessment = await self._assess_risks(stock_data, analysis_results)
        
        # 5. 最终决策
        final_decision = await self._make_final_decision(
            stock_data, analysis_results, integrated_report, risk_assessment
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
        """准备数据"""
        logger.info("准备市场数据...")
        
        symbols = config.get("symbols", [])
        timeframe = config.get("timeframe", "1d")
        start_date = config.get("start_date")
        end_date = config.get("end_date", datetime.now())
        
        # 获取股票数据
        stock_data_list = []
        for symbol in symbols:
            try:
                data = await self.data_service.get_stock_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date
                )
                if data is not None:
                    stock_data_list.append(data)
                    logger.info(f"获取数据成功: {symbol}")
                else:
                    logger.warning(f"获取数据返回None: {symbol}")
            except Exception as e:
                logger.error(f"获取数据失败 {symbol}: {e}")
        
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
        
        return organized_results
    
    async def _integrate_reports(self, analysis_results: Dict[str, List[AnalysisResult]]) -> Dict[str, Any]:
        """整合分析报告"""
        logger.info("整合分析报告...")
        
        integrated_report = {}
        for symbol, results in analysis_results.items():
            if not results:
                continue
            
            # 计算平均分数
            avg_score = sum(r.score for r in results) / len(results)
            avg_confidence = sum(r.confidence for r in results) / len(results)
            
            # 收集所有洞察和建议
            all_insights = []
            all_recommendations = []
            all_risks = []
            
            for result in results:
                all_insights.extend(result.insights)
                all_recommendations.extend(result.recommendations)
                all_risks.extend(result.risks)
            
            integrated_report[symbol] = {
                "avg_score": avg_score,
                "avg_confidence": avg_confidence,
                "insights": list(set(all_insights)),  # 去重
                "recommendations": list(set(all_recommendations)),
                "risks": list(set(all_risks)),
                "analysis_count": len(results)
            }
        
        return integrated_report
    
    async def _assess_risks(self, stock_data: List[StockData], 
                          analysis_results: Dict[str, List[AnalysisResult]]) -> Dict[str, Any]:
        """风险评估"""
        logger.info("进行风险评估...")
        
        # 这里应该实现实际的风险评估逻辑
        # 目前返回模拟数据
        
        risk_assessment = {}
        for stock in stock_data:
            if stock is None:
                continue
            
            risk_assessment[stock.symbol] = {
                "market_risk": 0.3,
                "liquidity_risk": 0.2,
                "credit_risk": 0.1,
                "operational_risk": 0.15,
                "overall_risk_score": 0.2,  # 综合风险分数
                "risk_level": "LOW",  # 风险等级
                "recommendations": ["建议持有", "设置止损"]
            }
        
        return risk_assessment
    
    async def _make_final_decision(self, stock_data: List[StockData],
                                 analysis_results: Dict[str, List[AnalysisResult]],
                                 integrated_report: Dict[str, Any],
                                 risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """最终决策"""
        logger.info("进行最终决策...")
        
        final_decisions = {}
        for stock in stock_data:
            if stock is None:
                continue
            
            symbol = stock.symbol
            
            # 获取分析结果和风险评估
            analysis = integrated_report.get(symbol, {})
            risk = risk_assessment.get(symbol, {})
            
            # 决策逻辑
            avg_score = analysis.get("avg_score", 0)
            risk_score = risk.get("overall_risk_score", 1)
            
            # 决策阈值
            if avg_score > 70 and risk_score < 0.3:
                decision = "BUY"
                confidence = 0.8
            elif avg_score < 30 or risk_score > 0.7:
                decision = "SELL"
                confidence = 0.7
            else:
                decision = "HOLD"
                confidence = 0.6
            
            final_decisions[symbol] = {
                "decision": decision,
                "confidence": confidence,
                "reason": f"分析评分: {avg_score:.1f}, 风险评分: {risk_score:.2f}",
                "timestamp": datetime.now().isoformat()
            }
        
        return final_decisions
    
    async def _generate_trading_signals(self, final_decision: Dict[str, Any]) -> List[TradingSignal]:
        """生成交易信号"""
        logger.info("生成交易信号...")
        
        trading_signals = []
        for symbol, decision in final_decision.items():
            if decision["decision"] == "HOLD":
                continue
            
            # 创建交易信号
            signal = TradingSignal(
                symbol=symbol,
                action=decision["decision"],
                price=100.0,  # 模拟价格
                quantity=100,  # 模拟数量
                reason=decision["reason"],
                confidence=decision["confidence"],
                stop_loss=90.0 if decision["decision"] == "BUY" else 110.0,
                take_profit=120.0 if decision["decision"] == "BUY" else 80.0,
                expiry=datetime.now() + timedelta(days=7)
            )
            trading_signals.append(signal)
        
        return trading_signals
    
    async def execute_trades(self, trading_signals: List[TradingSignal], 
                           capital: float = 100000) -> Dict[str, Any]:
        """执行交易"""
        logger.info(f"执行交易，资金: ¥{capital:,.2f}")
        
        # 这里应该实现实际的交易执行逻辑
        # 目前返回模拟数据
        
        executed_trades = []
        total_investment = 0
        
        for signal in trading_signals:
            if total_investment + signal.price * signal.quantity > capital * 0.8