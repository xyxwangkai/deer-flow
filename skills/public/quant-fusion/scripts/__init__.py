#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化融合系统 - 脚本模块
融合Qlib、AlphaCouncil、TradingAgents的超级智能体系统
"""

from .core import (
    QuantFusionSystem,
    StockData,
    AnalysisResult,
    TradingSignal,
    MarketType,
    AnalysisType
)

from .data_manager import (
    DataManager,
    RDAAgent
)

from .trading_executor import (
    TradingExecutor,
    Order,
    Position,
    Account,
    BrokerType
)

from .risk_management import (
    RiskManager,
    RiskMetrics,
    RiskLimit,
    RiskAlert
)

from .agents.council import (
    AlphaCouncilSystem,
    AgentRole,
    AnalysisResult as CouncilAnalysisResult,
    CouncilDecision
)

__version__ = "1.0.0"
__author__ = "量化融合团队"
__description__ = "融合Qlib、AlphaCouncil、TradingAgents的超级量化交易智能体系统"

__all__ = [
    # 核心系统
    "QuantFusionSystem",
    "StockData",
    "AnalysisResult",
    "TradingSignal",
    "MarketType",
    "AnalysisType",
    
    # 数据管理
    "DataManager",
    "RDAAgent",
    
    # 交易执行
    "TradingExecutor",
    "Order",
    "Position",
    "Account",
    "BrokerType",
    
    # 风险管理
    "RiskManager",
    "RiskMetrics",
    "RiskLimit",
    "RiskAlert",
    
    # AlphaCouncil智能体
    "AlphaCouncilSystem",
    "AgentRole",
    "CouncilAnalysisResult",
    "CouncilDecision",
]