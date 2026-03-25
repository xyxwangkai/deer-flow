#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlphaCouncil多智能体系统
基于AlphaCouncil项目的多智能体决策框架
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import json

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """智能体角色枚举"""
    ANALYST_FUNDAMENTAL = "基本面分析师"
    ANALYST_TECHNICAL = "技术面分析师"
    ANALYST_SENTIMENT = "情绪面分析师"
    ANALYST_CAPITAL = "资金面分析师"
    ANALYST_MACRO = "宏观分析师"
    ANALYST_RISK = "风险分析师"
    DIRECTOR_INTEGRATION = "整合总监"
    DIRECTOR_RISK = "风控总监"
    MANAGER_GENERAL = "总经理"
    TRADER_EXECUTION = "交易员"
    TRADER_ALGORITHMIC = "算法交易员"
    RESEARCHER_QUANT = "量化研究员"
    RESEARCHER_AI = "AI研究员"


class DecisionLevel(Enum):
    """决策层级枚举"""
    ANALYST = "分析师"
    DIRECTOR = "总监"
    MANAGER = "总经理"
    EXECUTIVE = "执行层"


@dataclass
class AgentProfile:
    """智能体档案"""
    agent_id: str
    role: AgentRole
    expertise: List[str]
    confidence: float  # 0-1之间的置信度
    performance_history: List[float] = field(default_factory=list)
    decision_weight: float = 1.0
    personality: Dict[str, float] = field(default_factory=dict)  # 风险偏好、激进程度等


@dataclass
class AnalysisResult:
    """分析结果"""
    agent_id: str
    role: AgentRole
    symbol: str
    analysis_type: str
    confidence: float
    recommendation: str  # BUY, SELL, HOLD
    reasoning: str
    supporting_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CouncilDecision:
    """委员会决策"""
    decision_id: str
    symbol: str
    final_recommendation: str
    confidence: float
    reasoning: str
    analyst_votes: Dict[str, str]  # agent_id -> recommendation
    director_votes: Dict[str, str]
    manager_decision: Optional[str] = None
    execution_plan: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


class AlphaCouncilAgent:
    """AlphaCouncil智能体基类"""
    
    def __init__(self, agent_id: str, role: AgentRole, config: Dict[str, Any]):
        """
        初始化智能体
        
        Args:
            agent_id: 智能体ID
            role: 智能体角色
            config: 智能体配置
        """
        self.agent_id = agent_id
        self.role = role
        self.config = config
        self.profile = AgentProfile(
            agent_id=agent_id,
            role=role,
            expertise=config.get("expertise", []),
            confidence=config.get("initial_confidence", 0.7),
            personality=config.get("personality", {})
        )
        
        # 初始化分析能力
        self.analysis_capabilities = self._init_capabilities()
        
        logger.info(f"智能体初始化: {agent_id} ({role.value})")
    
    def _init_capabilities(self) -> Dict[str, Any]:
        """初始化分析能力"""
        capabilities = {}
        
        if self.role == AgentRole.ANALYST_FUNDAMENTAL:
            capabilities["financial_statement_analysis"] = True
            capabilities["valuation_models"] = ["DCF", "Comparables", "Dividend_Discount"]
            capabilities["industry_analysis"] = True
            
        elif self.role == AgentRole.ANALYST_TECHNICAL:
            capabilities["technical_indicators"] = ["MA", "RSI", "MACD", "Bollinger_Bands"]
            capabilities["chart_patterns"] = True
            capabilities["volume_analysis"] = True
            
        elif self.role == AgentRole.ANALYST_SENTIMENT:
            capabilities["news_sentiment"] = True
            capabilities["social_media_analysis"] = True
            capabilities["market_sentiment"] = True
            
        elif self.role == AgentRole.ANALYST_CAPITAL:
            capabilities["institutional_flow"] = True
            capabilities["retail_flow"] = True
            capabilities["margin_trading"] = True
            
        elif self.role == AgentRole.ANALYST_MACRO:
            capabilities["economic_indicators"] = True
            capabilities["policy_analysis"] = True
            capabilities["global_markets"] = True
            
        elif self.role == AgentRole.ANALYST_RISK:
            capabilities["risk_assessment"] = True
            capabilities["var_calculation"] = True
            capabilities["stress_testing"] = True
            
        elif self.role == AgentRole.DIRECTOR_INTEGRATION:
            capabilities["consensus_building"] = True
            capabilities["conflict_resolution"] = True
            capabilities["weighted_decision"] = True
            
        elif self.role == AgentRole.DIRECTOR_RISK:
            capabilities["risk_oversight"] = True
            capabilities["compliance_check"] = True
            capabilities["exposure_management"] = True
            
        elif self.role == AgentRole.MANAGER_GENERAL:
            capabilities["strategic_decision"] = True
            capabilities["resource_allocation"] = True
            capabilities["performance_oversight"] = True
            
        elif self.role in [AgentRole.TRADER_EXECUTION, AgentRole.TRADER_ALGORITHMIC]:
            capabilities["order_execution"] = True
            capabilities["market_making"] = True
            capabilities["algorithmic_trading"] = True
            
        elif self.role in [AgentRole.RESEARCHER_QUANT, AgentRole.RESEARCHER_AI]:
            capabilities["model_development"] = True
            capabilities["backtesting"] = True
            capabilities["optimization"] = True
        
        return capabilities
    
    async def analyze(self, data: Any, context: Dict[str, Any]) -> AnalysisResult:
        """
        执行分析
        
        Args:
            data: 分析数据 (可以是Dict或StockData对象)
            context: 分析上下文
            
        Returns:
            分析结果
        """
        logger.info(f"{self.agent_id} 开始分析: {context.get('symbol', 'Unknown')}")
        
        try:
            # 将数据转换为字典格式
            data_dict = self._convert_to_dict(data)
            
            # 根据角色调用不同的分析方法
            if self.role == AgentRole.ANALYST_FUNDAMENTAL:
                result = await self._analyze_fundamental(data_dict, context)
            elif self.role == AgentRole.ANALYST_TECHNICAL:
                result = await self._analyze_technical(data_dict, context)
            elif self.role == AgentRole.ANALYST_SENTIMENT:
                result = await self._analyze_sentiment(data_dict, context)
            elif self.role == AgentRole.ANALYST_CAPITAL:
                result = await self._analyze_capital(data_dict, context)
            elif self.role == AgentRole.ANALYST_MACRO:
                result = await self._analyze_macro(data_dict, context)
            elif self.role == AgentRole.ANALYST_RISK:
                result = await self._analyze_risk(data_dict, context)
            else:
                result = await self._analyze_general(data_dict, context)
            
            # 更新智能体表现记录
            self._update_performance(result.confidence)
            
            logger.info(f"{self.agent_id} 分析完成: {result.recommendation} (置信度: {result.confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"{self.agent_id} 分析失败: {e}")
            return self._create_error_result({"symbol": context.get("symbol", "Unknown")}, str(e))
    
    def _convert_to_dict(self, data: Any) -> Dict[str, Any]:
        """将数据转换为字典格式"""
        if isinstance(data, dict):
            return data
        
        # 尝试从StockData对象提取信息
        try:
            # 检查是否有symbol属性
            if hasattr(data, 'symbol'):
                symbol = data.symbol
            else:
                symbol = "Unknown"
            
            # 检查是否有price属性
            if hasattr(data, 'price'):
                price = data.price
            else:
                price = 100.0
            
            # 检查是否有indicators属性
            if hasattr(data, 'indicators'):
                indicators = data.indicators
            else:
                indicators = {}
            
            # 检查是否有fundamentals属性
            if hasattr(data, 'fundamentals'):
                fundamentals = data.fundamentals
            else:
                fundamentals = {}
            
            # 构建数据字典
            data_dict = {
                "symbol": symbol,
                "price": price,
                "price_data": {
                    "current": price,
                    "ma_20": indicators.get('ma20', price * 0.95),
                    "ma_60": indicators.get('ma60', price * 0.9),
                    "rsi": indicators.get('rsi', 50),
                    "macd_signal": indicators.get('macd', 0)
                },
                "pe_ratio": fundamentals.get('pe_ratio', 20),
                "pb_ratio": fundamentals.get('pb_ratio', 2),
                "roe": fundamentals.get('roe', 0.15),
                "revenue_growth": fundamentals.get('revenue_growth', 0.1),
                "sentiment_data": {
                    "news": random.uniform(-0.5, 0.5),
                    "social": random.uniform(-0.5, 0.5),
                    "market": random.uniform(-0.5, 0.5)
                },
                "capital_data": {
                    "institutional": random.uniform(-1000000, 1000000),
                    "retail": random.uniform(-500000, 500000),
                    "margin": random.uniform(-100000, 100000)
                },
                "macro_data": {
                    "gdp_growth": random.uniform(0.02, 0.08),
                    "inflation": random.uniform(0.01, 0.05),
                    "interest_rate": random.uniform(0.01, 0.04)
                },
                "risk_data": {
                    "volatility": random.uniform(0.1, 0.4),
                    "beta": random.uniform(0.5, 1.5),
                    "sharpe_ratio": random.uniform(-0.5, 1.5)
                }
            }
            
            return data_dict
            
        except Exception as e:
            logger.warning(f"数据转换失败，使用默认数据: {e}")
            return {
                "symbol": "Unknown",
                "price": 100.0,
                "price_data": {"current": 100.0, "ma_20": 95.0, "ma_60": 90.0, "rsi": 50, "macd_signal": 0},
                "pe_ratio": 20,
                "pb_ratio": 2,
                "roe": 0.15,
                "revenue_growth": 0.1
            }
    
    async def integrate_reports(self, analysis_results: Dict[str, List[AnalysisResult]]) -> Dict[str, Any]:
        """整合分析报告"""
        logger.info(f"{self.agent_id} 开始整合分析报告")
        
        if not analysis_results:
            return {"error": "无分析结果可整合", "status": "empty"}
        
        integrated_report = {
            "timestamp": datetime.now().isoformat(),
            "symbols_analyzed": list(analysis_results.keys()),
            "total_analyses": sum(len(results) for results in analysis_results.values()),
            "symbol_recommendations": {},
            "overall_summary": {}
        }
        
        # 为每个股票计算整合推荐
        for symbol, results in analysis_results.items():
            if not results:
                integrated_report["symbol_recommendations"][symbol] = {
                    "recommendation": "HOLD",
                    "confidence": 0.1,
                    "reasoning": "无有效分析结果"
                }
                continue
            
            # 计算投票统计
            recommendations = {"BUY": 0, "HOLD": 0, "SELL": 0}
            total_confidence = 0
            
            for result in results:
                recommendations[result.recommendation] += 1
                total_confidence += result.confidence
            
            # 确定最终推荐
            final_recommendation = max(recommendations.items(), key=lambda x: x[1])[0]
            avg_confidence = total_confidence / len(results) if results else 0.5
            
            # 生成理由
            reasoning = f"基于{len(results)}个分析，投票结果: {recommendations}"
            
            integrated_report["symbol_recommendations"][symbol] = {
                "recommendation": final_recommendation,
                "confidence": avg_confidence,
                "reasoning": reasoning,
                "vote_distribution": recommendations
            }
        
        # 计算整体总结
        if integrated_report["symbol_recommendations"]:
            buy_count = sum(1 for rec in integrated_report["symbol_recommendations"].values() 
                          if rec["recommendation"] == "BUY")
            sell_count = sum(1 for rec in integrated_report["symbol_recommendations"].values() 
                           if rec["recommendation"] == "SELL")
            hold_count = sum(1 for rec in integrated_report["symbol_recommendations"].values() 
                           if rec["recommendation"] == "HOLD")
            
            integrated_report["overall_summary"] = {
                "buy_count": buy_count,
                "sell_count": sell_count,
                "hold_count": hold_count,
                "total_symbols": len(integrated_report["symbol_recommendations"]),
                "market_sentiment": "BULLISH" if buy_count > sell_count else 
                                  "BEARISH" if sell_count > buy_count else "NEUTRAL"
            }
        
        logger.info(f"{self.agent_id} 整合报告完成，分析 {len(integrated_report['symbol_recommendations'])} 个标的")
        return integrated_report
    
    async def assess_risks(self, integrated_report: Dict[str, Any]) -> Dict[str, Any]:
        """风险评估"""
        logger.info(f"{self.agent_id} 开始风险评估")
        
        if not integrated_report or "error" in integrated_report:
            return {
                "risk_level": "HIGH",
                "reasoning": "无有效整合报告，风险未知",
                "recommendations": ["暂停交易", "重新评估"]
            }
        
        # 提取关键信息
        symbols_analyzed = integrated_report.get("symbols_analyzed", [])
        symbol_recommendations = integrated_report.get("symbol_recommendations", {})
        overall_summary = integrated_report.get("overall_summary", {})
        
        # 风险评估逻辑
        total_symbols = len(symbols_analyzed)
        if total_symbols == 0:
            return {
                "risk_level": "HIGH",
                "reasoning": "未分析任何标的，风险未知",
                "recommendations": ["暂停交易"]
            }
        
        # 计算风险指标
        buy_ratio = overall_summary.get("buy_count", 0) / total_symbols if total_symbols > 0 else 0
        sell_ratio = overall_summary.get("sell_count", 0) / total_symbols if total_symbols > 0 else 0
        
        # 确定风险等级
        if sell_ratio > 0.5:
            risk_level = "HIGH"
            reasoning = f"超过50%的标的被建议卖出 ({sell_ratio:.1%})"
        elif buy_ratio > 0.7:
            risk_level = "LOW"
            reasoning = f"超过70%的标的被建议买入 ({buy_ratio:.1%})，市场情绪积极"
        elif buy_ratio > sell_ratio:
            risk_level = "MEDIUM_LOW"
            reasoning = f"买入建议多于卖出建议 ({buy_ratio:.1%} vs {sell_ratio:.1%})"
        elif sell_ratio > buy_ratio:
            risk_level = "MEDIUM_HIGH"
            reasoning = f"卖出建议多于买入建议 ({sell_ratio:.1%} vs {buy_ratio:.1%})"
        else:
            risk_level = "MEDIUM"
            reasoning = "买入卖出建议平衡，市场情绪中性"
        
        # 生成风险建议
        recommendations = []
        if risk_level == "HIGH":
            recommendations = ["立即停止新开仓", "考虑减仓", "加强监控"]
        elif risk_level == "MEDIUM_HIGH":
            recommendations = ["谨慎开仓", "设置严格止损", "降低仓位"]
        elif risk_level == "MEDIUM":
            recommendations = ["正常交易", "保持风险控制", "定期评估"]
        elif risk_level == "MEDIUM_LOW":
            recommendations = ["适度增加仓位", "保持风险控制", "监控市场变化"]
        elif risk_level == "LOW":
            recommendations = ["积极交易", "适度提高仓位", "把握机会"]
        
        risk_assessment = {
            "risk_level": risk_level,
            "reasoning": reasoning,
            "recommendations": recommendations,
            "metrics": {
                "total_symbols": total_symbols,
                "buy_ratio": buy_ratio,
                "sell_ratio": sell_ratio,
                "market_sentiment": overall_summary.get("market_sentiment", "NEUTRAL")
            }
        }
        
        logger.info(f"{self.agent_id} 风险评估完成: {risk_level}")
        return risk_assessment
    
    async def _analyze_fundamental(self, data: Dict[str, Any], context: Dict[str, Any]) -> AnalysisResult:
        """基本面分析"""
        symbol = data.get("symbol", "Unknown")
        price = data.get("price", 100.0)
        
        # 获取基本面数据
        pe_ratio = data.get("pe_ratio", 20)
        pb_ratio = data.get("pb_ratio", 2)
        roe = data.get("roe", 0.15)
        revenue_growth = data.get("revenue_growth", 0.1)
        
        # 分析逻辑
        score = 50.0
        reasoning = []
        
        # PE分析
        if pe_ratio < 15:
            score += 15
            reasoning.append(f"PE较低({pe_ratio:.1f})，估值合理")
        elif pe_ratio > 30:
            score -= 10
            reasoning.append(f"PE较高({pe_ratio:.1f})，估值偏高")
        
        # ROE分析
        if roe > 0.2:
            score += 20
            reasoning.append(f"ROE较高({roe:.1%})，盈利能力优秀")
        elif roe < 0.1:
            score -= 10
            reasoning.append(f"ROE较低({roe:.1%})，盈利能力一般")
        
        # 收入增长分析
        if revenue_growth > 0.2:
            score += 15
            reasoning.append(f"收入增长强劲({revenue_growth:.1%})")
        elif revenue_growth < 0:
            score -= 15
            reasoning.append(f"收入负增长({revenue_growth:.1%})")
        
        # 确定推荐
        if score >= 70:
            recommendation = "BUY"
        elif score >= 40:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"
        
        confidence = min(0.9, max(0.3, score / 100))
        
        return AnalysisResult(
            agent_id=self.agent_id,
            role=self.role,
            symbol=symbol,
            analysis_type="基本面分析",
            confidence=confidence,
            recommendation=recommendation,
            reasoning="; ".join(reasoning),
            supporting_data={
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "roe": roe,
                "revenue_growth": revenue_growth,
                "score": score
            }
        )
    
    async def _analyze_technical(self, data: Dict[str, Any], context: Dict[str, Any]) -> AnalysisResult:
        """技术面分析"""
        symbol = data.get("symbol", "Unknown")
        price = data.get("price", 100.0)
        
        # 获取技术指标
        price_data = data.get("price_data", {})
        ma_20 = price_data.get("ma_20", price * 0.95)
        ma_60 = price_data.get("ma_60", price * 0.9)
        rsi = price_data.get("rsi", 50)
        macd_signal = price_data.get("macd_signal", 0)
        
        # 分析逻辑
        score = 50.0
        reasoning = []
        
        # 均线分析
        if price > ma_20 > ma_60:
            score += 20
            reasoning.append(f"价格在均线之上，多头排列")
        elif price < ma_20 < ma_60:
            score -= 15
            reasoning.append(f"价格在均线之下，空头排列")
        
        # RSI分析
        if rsi > 70:
            score -= 10
            reasoning.append(f"RSI超买({rsi:.1f})")
        elif rsi < 30:
            score += 10
            reasoning.append(f"RSI超卖({rsi:.1f})")
        
        # MACD分析
        if macd_signal > 0:
            score += 10
            reasoning.append(f"MACD金叉信号")
        elif macd_signal < 0:
            score -= 5
            reasoning.append(f"MACD死叉信号")
        
        # 确定推荐
        if score >= 70:
            recommendation = "BUY"
        elif score >= 40:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"
        
        confidence = min(0.9, max(0.3, score / 100))
        
        return AnalysisResult(
            agent_id=self.agent_id,
            role=self.role,
            symbol=symbol,
            analysis_type="技术面分析",
            confidence=confidence,
            recommendation=recommendation,
            reasoning="; ".join(reasoning),
            supporting_data={
                "price": price,
                "ma_20": ma_20,
                "ma_60": ma_60,
                "rsi": rsi,
                "macd": macd_signal,
                "score": score
            }
        )
    
    async def _analyze_sentiment(self, data: Dict[str, Any], context: Dict[str, Any]) -> AnalysisResult:
        """情绪面分析"""
        symbol = data.get("symbol", "Unknown")
        
        # 获取情绪数据
        sentiment_data = data.get("sentiment_data", {})
        news_sentiment = sentiment_data.get("news", 0)
        social_sentiment = sentiment_data.get("social", 0)
        market_sentiment = sentiment_data.get("market", 0)
        
        # 计算综合情绪
        total_sentiment = (news_sentiment + social_sentiment + market_sentiment) / 3
        
        # 分析逻辑
        score = 50.0 + total_sentiment * 50
        reasoning = []
        
        if total_sentiment > 0.3:
            score += 20
            recommendation = "BUY"
            reasoning.append(f"情绪非常积极({total_sentiment:.2f})")
        elif total_sentiment > 0.1:
            score += 10
            recommendation = "BUY"
            reasoning.append(f"情绪积极({total_sentiment:.2f})")
        elif total_sentiment < -0.3:
            score -= 20
            recommendation = "SELL"
            reasoning.append(f"情绪非常消极({total_sentiment:.2f})")
        elif total_sentiment < -0.1:
            score -= 10
            recommendation = "SELL"
            reasoning.append(f"情绪消极({total_sentiment:.2f})")
        else:
            recommendation = "HOLD"
            reasoning.append(f"情绪中性({total_sentiment:.2f})")
        
        confidence = min(0.9, max(0.3, score / 100))
        
        return AnalysisResult(
            agent_id=self.agent_id,
            role=self.role,
            symbol=symbol,
            analysis_type="情绪面分析",
            confidence=confidence,
            recommendation=recommendation,
            reasoning="; ".join(reasoning),
            supporting_data={
                "news_sentiment": news_sentiment,
                "social_sentiment": social_sentiment,
                "market_sentiment": market_sentiment,
                "total_sentiment": total_sentiment,
                "score": score
            }
        )
    
    async def _analyze_capital(self, data: Dict[str, Any], context: Dict[str, Any]) -> AnalysisResult:
        """资金面分析"""
        symbol = data.get("symbol", "Unknown")
        
        # 获取资金流数据
        capital_data = data.get("capital_data", {})
        institutional_flow = capital_data.get("institutional", 0)
        retail_flow = capital_data.get("retail", 0)
        margin_flow = capital_data.get("margin", 0)
        
        # 分析逻辑
        score = 50.0
        reasoning = []
        
        # 机构资金分析
        if institutional_flow > 1000000:
            score += 20
            reasoning.append(f"机构资金大幅流入({institutional_flow:,.0f})")
        elif institutional_flow > 0:
            score += 10
            reasoning.append(f"机构资金流入({institutional_flow:,.0f})")
        elif institutional_flow < -1000000:
            score -= 20
            reasoning.append(f"机构资金大幅流出({-institutional_flow:,.0f})")
        elif institutional_flow < 0:
            score -= 10
            reasoning.append(f"机构资金流出({-institutional_flow:,.0f})")
        
        # 融资融券分析
        if margin_flow > 500000:
            score += 10
            reasoning.append(f"融资买入活跃({margin_flow:,.0f})")
        elif margin_flow < -500000:
            score -= 10
            reasoning.append(f"融券卖出活跃({-margin_flow:,.0f})")
        
        # 确定推荐
        if score >= 70:
            recommendation = "BUY"
        elif score >= 40:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"
        
        confidence = min(0.9, max(0.3, score / 100))
        
        return AnalysisResult(
            agent_id=self.agent_id,
            role=self.role,
            symbol=symbol,
            analysis_type="资金面分析",
            confidence=confidence,
            recommendation=recommendation,
            reasoning="; ".join(reasoning),
            supporting_data={
                "institutional_flow": institutional_flow,
                "retail_flow": retail_flow,
                "margin_flow": margin_flow,
                "score": score
            }
        )
    
    async def _analyze_macro(self, data: Dict[str, Any], context: Dict[str, Any]) -> AnalysisResult:
        """宏观面分析"""
        symbol = data.get("symbol", "Unknown")
        
        # 获取宏观数据
        macro_data = data.get("macro_data", {})
        gdp_growth = macro_data.get("gdp_growth", 0.05)
        inflation = macro_data.get("inflation", 0.02)
        interest_rate = macro_data.get("interest_rate", 0.03)
        
        # 分析逻辑
        score = 50.0
        reasoning = []
        
        # GDP增长分析
        if gdp_growth > 0.06:
            score += 15
            reasoning.append(f"经济强劲增长({gdp_growth:.1%})")
        elif gdp_growth < 0.03:
            score -= 10
            reasoning.append(f"经济增长放缓({gdp_growth:.1%})")
        
        # 通胀分析
        if inflation > 0.04:
            score -= 10
            reasoning.append(f"通胀较高({inflation:.1%})")
        elif inflation < 0.01:
            score += 5
            reasoning.append(f"通胀温和({inflation:.1%})")
        
        # 利率分析
        if interest_rate > 0.05:
            score -= 10
            reasoning.append(f"利率较高({interest_rate:.1%})")
        elif interest_rate < 0.02:
            score += 10
            reasoning.append(f"利率较低({interest_rate:.1%})")
        
        # 确定推荐
        if score >= 70:
            recommendation = "BUY"
        elif score >= 40:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"
        
        confidence = min(0.9, max(0.3, score / 100))
        
        return AnalysisResult(
            agent_id=self.agent_id,
            role=self.role,
            symbol=symbol,
            analysis_type="宏观面分析",
            confidence=confidence,
            recommendation=recommendation,
            reasoning="; ".join(reasoning),
            supporting_data={
                "gdp_growth": gdp_growth,
                "inflation": inflation,
                "interest_rate": interest_rate,
                "score": score
            }
        )
    
    async def _analyze_risk(self, data: Dict[str, Any], context: Dict[str, Any]) -> AnalysisResult:
        """风险分析"""
        symbol = data.get("symbol", "Unknown")
        
        # 获取风险数据
        risk_data = data.get("risk_data", {})
        volatility = risk_data.get("volatility", 0.2)
        beta = risk_data.get("beta", 1.0)
        sharpe_ratio = risk_data.get("sharpe_ratio", 0.5)
        
        # 分析逻辑
        score = 50.0
        reasoning = []
        
        # 波动率分析
        if volatility > 0.3:
            score -= 15
            reasoning.append(f"波动率较高({volatility:.1%})")
        elif volatility < 0.15:
            score += 10
            reasoning.append(f"波动率较低({volatility:.1%})")
        
        # Beta分析
        if beta > 1.3:
            score -= 10
            reasoning.append(f"市场敏感度高(Beta={beta:.2f})")
        elif beta < 0.7:
            score += 5
            reasoning.append(f"市场敏感度低(Beta={beta:.2f})")
        
        # 夏普比率分析
        if sharpe_ratio > 1.0:
            score += 20
            reasoning.append(f"风险调整后收益高(Sharpe={sharpe_ratio:.2f})")
        elif sharpe_ratio < 0:
            score -= 15
            reasoning.append(f"风险调整后收益为负(Sharpe={sharpe_ratio:.2f})")
        
        # 确定推荐
        if score >= 70:
            recommendation = "BUY"
        elif score >= 40:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"
        
        confidence = min(0.9, max(0.3, score / 100))
        
        return AnalysisResult(
            agent_id=self.agent_id,
            role=self.role,
            symbol=symbol,
            analysis_type="风险分析",
            confidence=confidence,
            recommendation=recommendation,
            reasoning="; ".join(reasoning),
            supporting_data={
                "volatility": volatility,
                "beta": beta,
                "sharpe_ratio": sharpe_ratio,
                "score": score
            }
        )
    
    async def _analyze_general(self, data: Dict[str, Any], context: Dict[str, Any]) -> AnalysisResult:
        """通用分析"""
        symbol = data.get("symbol", "Unknown")
        price = data.get("price", 100.0)
        
        # 简单分析逻辑
        score = 60.0 + random.uniform(-20, 20)
        
        if score >= 70:
            recommendation = "BUY"
        elif score >= 40:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"
        
        confidence = min(0.9, max(0.3, score / 100))
        
        return AnalysisResult(
            agent_id=self.agent_id,
            role=self.role,
            symbol=symbol,
            analysis_type="通用分析",
            confidence=confidence,
            recommendation=recommendation,
            reasoning=f"基于通用分析模型，得分{score:.1f}",
            supporting_data={
                "price": price,
                "score": score
            }
        )
    
    def _create_error_result(self, context: Dict[str, Any], error_msg: str) -> AnalysisResult:
        """创建错误结果"""
        return AnalysisResult(
            agent_id=self.agent_id,
            role=self.role,
            symbol=context.get("symbol", "Unknown"),
            analysis_type="错误分析",
            confidence=0.1,
            recommendation="HOLD",
            reasoning=f"分析失败: {error_msg}",
            supporting_data={"error": error_msg}
        )
    
    def _update_performance(self, confidence: float):
        """更新智能体表现记录"""
        self.profile.performance_history.append(confidence)
        if len(self.profile.performance_history) > 10:
            self.profile.performance_history.pop(0)
        
        # 更新置信度
        avg_confidence = sum(self.profile.performance_history) / len(self.profile.performance_history)
        self.profile.confidence = avg_confidence
    
    async def make_decision(self, integrated_report: Dict[str, Any], risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        做出最终决策（总经理角色使用）
        
        Args:
            integrated_report: 整合报告
            risk_assessment: 风险评估
            
        Returns:
            最终决策
        """
        logger.info(f"{self.agent_id} 开始做出最终决策")
        
        # 获取整合决策
        decision = integrated_report.get("decision", "HOLD")
        confidence = integrated_report.get("confidence", 0.5)
        reasoning = integrated_report.get("reasoning", "")
        
        # 考虑风险因素
        risk_level = risk_assessment.get("risk_level", "MEDIUM")
        risk_score = risk_assessment.get("risk_score", 0.5)
        
        # 根据风险调整决策
        if risk_level == "HIGH" and decision == "BUY":
            decision = "HOLD"
            confidence = max(0.3, confidence - 0.2)
            reasoning += f"\n⚠️ 风险等级高({risk_score:.2f})，将BUY调整为HOLD"
        elif risk_level == "VERY_HIGH":
            decision = "SELL"
            confidence = 0.8
            reasoning = f"⚠️ 风险等级非常高({risk_score:.2f})，建议卖出"
        
        # 构建最终决策
        final_decision = {
            "action": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "agent_role": self.role.value
        }
        
        logger.info(f"{self.agent_id} 最终决策完成: {decision} (置信度: {confidence:.2f})")
        return final_decision


class AlphaCouncilSystem:
    """AlphaCouncil多智能体系统"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化AlphaCouncil多智能体系统
        
        Args:
            config: 配置字典，包含智能体配置
        """
        self.config = config
        self.agents = {}
        self._init_agents()
        logger.info("AlphaCouncil系统初始化完成")
    
    def _init_agents(self):
        """初始化所有智能体"""
        agents_config = self.config.get("agents", {})
        
        for agent_id, agent_config in agents_config.items():
            # 根据agent_id确定角色
            if "analyst_fundamental" in agent_id:
                role = AgentRole.ANALYST_FUNDAMENTAL
            elif "analyst_technical" in agent_id:
                role = AgentRole.ANALYST_TECHNICAL
            elif "analyst_sentiment" in agent_id:
                role = AgentRole.ANALYST_SENTIMENT
            elif "analyst_capital" in agent_id:
                role = AgentRole.ANALYST_CAPITAL
            elif "analyst_macro" in agent_id:
                role = AgentRole.ANALYST_MACRO
            elif "analyst_risk" in agent_id:
                role = AgentRole.ANALYST_RISK
            elif "director_integration" in agent_id:
                role = AgentRole.DIRECTOR_INTEGRATION
            elif "director_risk" in agent_id:
                role = AgentRole.DIRECTOR_RISK
            elif "manager_general" in agent_id:
                role = AgentRole.MANAGER_GENERAL
            elif "trader" in agent_id:
                role = AgentRole.TRADER_EXECUTION
            elif "researcher" in agent_id:
                role = AgentRole.RESEARCHER_QUANT
            elif "analyst" in agent_id:
                role = AgentRole.ANALYST_FUNDAMENTAL
            else:
                role = AgentRole.ANALYST_FUNDAMENTAL
            
            # 创建智能体
            agent = AlphaCouncilAgent(
                agent_id=agent_id,
                role=role,
                config=agent_config
            )
            self.agents[agent_id] = agent
    
    async def run_committee_decision(self, symbols: List[str]) -> Dict[str, Any]:
        """
        运行委员会决策流程
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            决策结果字典
        """
        logger.info(f"开始委员会决策流程，分析 {len(symbols)} 只股票")
        
        # 收集所有智能体的分析结果
        all_results = {}
        
        for symbol in symbols:
            symbol_results = {}
            
            # 每个智能体分析该股票
            for agent_id, agent in self.agents.items():
                try:
                    # 准备数据
                    data = {
                        "symbol": symbol,
                        "price": 100.0 + random.uniform(-10, 10),
                        "timestamp": datetime.now(),
                        "market_condition": "NORMAL"
                    }
                    
                    context = {
                        "symbol": symbol,
                        "timestamp": datetime.now(),
                        "market_condition": "NORMAL",
                        "data_type": "stock"
                    }
                    
                    # 执行分析
                    result = await agent.analyze(data, context)
                    symbol_results[agent_id] = result
                    
                except Exception as e:
                    logger.error(f"智能体 {agent_id} 分析失败: {e}")
                    symbol_results[agent_id] = None
            
            all_results[symbol] = symbol_results
        
        # 整合分析结果
        integrated_results = await self._integrate_director_decision(all_results)
        
        # 风险评估
        risk_assessment = await self._assess_committee_risk(all_results)
        
        # 最终决策
        final_decision = self._make_final_decision(integrated_results, risk_assessment)
        
        return {
            "decision": final_decision,
            "analysis_results": all_results,
            "integrated_results": integrated_results,
            "risk_assessment": risk_assessment
        }
    
    async def _integrate_director_decision(self, all_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """总监整合决策"""
        logger.info("总监整合决策...")
        
        # 查找整合总监
        integration_director = None
        for agent_id, agent in self.agents.items():
            if "director_integration" in agent_id or "integration" in agent_id:
                integration_director = agent
                break
        
        if not integration_director:
            logger.warning("未找到整合总监，使用默认整合逻辑")
            return self._default_integration(all_results)
        
        try:
            # 准备整合数据 - 转换为integrate_reports期望的格式
            from .council import AnalysisResult
            
            integration_data = {}
            for symbol, agent_results in all_results.items():
                # 将每个智能体的结果转换为AnalysisResult列表
                results_list = []
                for agent_id, result in agent_results.items():
                    if isinstance(result, dict) and "recommendation" in result:
                        analysis_result = AnalysisResult(
                            symbol=symbol,
                            agent_id=agent_id,
                            recommendation=result.get("recommendation", "HOLD"),
                            confidence=result.get("confidence", 0.5),
                            reasoning=result.get("reasoning", "无分析结果"),
                            timestamp=datetime.now()
                        )
                        results_list.append(analysis_result)
                
                if results_list:
                    integration_data[symbol] = results_list
            
            # 执行整合
            if integration_data:
                integrated_result = await integration_director.integrate_reports(integration_data)
                return integrated_result
            else:
                return self._default_integration(all_results)
            
        except Exception as e:
            logger.error(f"总监整合失败: {e}")
            return self._default_integration(all_results)
    
    def _default_integration(self, all_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """默认整合逻辑"""
        logger.info("使用默认整合逻辑...")
        
        # 统计所有智能体的推荐
        all_recommendations = []
        all_confidences = []
        
        for symbol, symbol_results in all_results.items():
            for agent_id, result in symbol_results.items():
                if result and hasattr(result, 'recommendation'):
                    all_recommendations.append(result.recommendation)
                    all_confidences.append(result.confidence)
        
        if not all_recommendations:
            return {
                "decision": "HOLD",
                "confidence": 0.5,
                "reasoning": "没有有效的分析结果",
                "summary": "所有智能体分析失败"
            }
        
        # 计算平均置信度
        avg_confidence = sum(all_confidences) / len(all_confidences)
        
        # 统计推荐类型
        buy_count = all_recommendations.count("BUY")
        sell_count = all_recommendations.count("SELL")
        hold_count = all_recommendations.count("HOLD")
        
        total_count = len(all_recommendations)
        
        # 根据多数原则决定
        if buy_count > sell_count and buy_count > hold_count:
            decision = "BUY"
        elif sell_count > buy_count and sell_count > hold_count:
            decision = "SELL"
        else:
            decision = "HOLD"
        
        return {
            "decision": decision,
            "confidence": avg_confidence,
            "reasoning": f"BUY: {buy_count}, SELL: {sell_count}, HOLD: {hold_count}",
            "summary": f"基于 {total_count} 个分析结果"
        }
    
    async def _assess_committee_risk(self, all_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """委员会风险评估"""
        logger.info("委员会风险评估...")
        
        # 查找风险总监
        risk_director = None
        for agent_id, agent in self.agents.items():
            if "director_risk" in agent_id or "risk" in agent_id:
                risk_director = agent
                break
        
        if not risk_director:
            logger.warning("未找到风险总监，使用默认风险评估")
            return self._default_risk_assessment(all_results)
        
        try:
            # 准备风险数据
            risk_data = {
                "all_results": all_results,
                "timestamp": datetime.now(),
                "market_condition": "NORMAL"
            }
            
            # 执行风险评估
            risk_assessment = await risk_director.assess_risks(risk_data)
            return risk_assessment
            
        except Exception as e:
            logger.error(f"风险评估失败: {e}")
            return self._default_risk_assessment(all_results)
    
    def _default_risk_assessment(self, all_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """默认风险评估"""
        # 统计风险信号
        total_symbols = len(all_results)
        total_analyses = sum(len(results) for results in all_results.values())
        
        # 计算风险指标
        risk_level = "LOW"
        reasoning = "默认风险评估"
        
        if total_symbols > 10:
            risk_level = "MEDIUM"
            reasoning = "分析股票数量较多"
        elif total_analyses > 50:
            risk_level = "MEDIUM_HIGH"
            reasoning = "分析任务繁重"
        
        return {
            "risk_level": risk_level,
            "reasoning": reasoning,
            "recommendations": ["保持风险控制", "定期评估"],
            "metrics": {
                "total_symbols": total_symbols,
                "total_analyses": total_analyses
            }
        }
    
    def _make_final_decision(self, integrated_results: Dict[str, Any], risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """做出最终决策"""
        logger.info("做出最终决策...")
        
        # 获取整合决策
        decision = integrated_results.get("decision", "HOLD")
        confidence = integrated_results.get("confidence", 0.5)
        reasoning = integrated_results.get("reasoning", "")
        
        # 考虑风险因素
        risk_level = risk_assessment.get("risk_level", "LOW")
        risk_reasoning = risk_assessment.get("reasoning", "")
        
        # 根据风险等级调整决策
        if risk_level in ["HIGH", "MEDIUM_HIGH"]:
            if decision == "BUY":
                decision = "HOLD"
                reasoning += f" | 因高风险({risk_level})调整为HOLD"
            elif decision == "SELL":
                confidence = min(confidence, 0.7)
        
        # 创建最终决策
        final_decision = {
            "action": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "risk_level": risk_level,
            "risk_reasoning": risk_reasoning,
            "timestamp": datetime.now()
        }
        
        logger.info(f"最终决策: {decision} (置信度: {confidence:.2f}, 风险等级: {risk_level})")
        return final_decision
    
    async def analyze_portfolio(self, portfolio: Dict[str, float]) -> Dict[str, Any]:
        """
        分析投资组合
        
        Args:
            portfolio: 投资组合字典 {股票代码: 权重}
            
        Returns:
            投资组合分析结果
        """
        logger.info(f"分析投资组合，包含 {len(portfolio)} 只股票")
        
        # 分析每只股票
        symbols = list(portfolio.keys())
        decision_result = await self.run_committee_decision(symbols)
        
        # 计算组合指标
        portfolio_metrics = self._calculate_portfolio_metrics(portfolio, decision_result)
        
        return {
            "portfolio_analysis": decision_result,
            "portfolio_metrics": portfolio_metrics,
            "recommendations": self._generate_portfolio_recommendations(portfolio_metrics)
        }
    
    def _calculate_portfolio_metrics(self, portfolio: Dict[str, float], decision_result: Dict[str, Any]) -> Dict[str, Any]:
        """计算投资组合指标"""
        total_weight = sum(portfolio.values())
        normalized_weights = {symbol: weight/total_weight for symbol, weight in portfolio.items()}
        
        # 获取每只股票的决策
        analysis_results = decision_result.get("analysis_results", {})
        integrated_results = decision_result.get("integrated_results", {})
        
        # 计算加权置信度
        weighted_confidence = 0
        buy_weight = 0
        sell_weight = 0
        hold_weight = 0
        
        for symbol, weight in normalized_weights.items():
            symbol_results = analysis_results.get(symbol, {})
            
            # 统计该股票的推荐
            symbol_buy = 0
            symbol_sell = 0
            symbol_hold = 0
            
            for agent_id, result in symbol_results.items():
                if result and hasattr(result, 'recommendation'):
                    if result.recommendation == "BUY":
                        symbol_buy += 1
                    elif result.recommendation == "SELL":
                        symbol_sell += 1
                    elif result.recommendation == "HOLD":
                        symbol_hold += 1
            
            total_agents = symbol_buy + symbol_sell + symbol_hold
            if total_agents > 0:
                if symbol_buy > symbol_sell and symbol_buy > symbol_hold:
                    buy_weight += weight
                elif symbol_sell > symbol_buy and symbol_sell > symbol_hold:
                    sell_weight += weight
                else:
                    hold_weight += weight
        
        # 计算整体置信度
        overall_confidence = integrated_results.get("confidence", 0.5)
        risk_level = decision_result.get("risk_assessment", {}).get("risk_level", "LOW")
        
        return {
            "total_symbols": len(portfolio),
            "buy_weight": buy_weight,
            "sell_weight": sell_weight,
            "hold_weight": hold_weight,
            "overall_confidence": overall_confidence,
            "risk_level": risk_level,
            "concentration": max(normalized_weights.values()) if normalized_weights else 0
        }
    
    def _generate_portfolio_recommendations(self, portfolio_metrics: Dict[str, Any]) -> List[str]:
        """生成投资组合建议"""
        recommendations = []
        
        buy_weight = portfolio_metrics.get("buy_weight", 0)
        sell_weight = portfolio_metrics.get("sell_weight", 0)
        hold_weight = portfolio_metrics.get("hold_weight", 0)
        concentration = portfolio_metrics.get("concentration", 0)
        risk_level = portfolio_metrics.get("risk_level", "LOW")
        
        # 基于权重分布的建议
        if buy_weight > 0.6:
            recommendations.append("投资组合偏多，建议保持或适度加仓")
        elif sell_weight > 0.6:
            recommendations.append("投资组合偏空，建议减仓或调整配置")
        
        # 基于集中度的建议
        if concentration > 0.3:
            recommendations.append("组合集中度过高，建议分散投资")
        
        # 基于风险等级的建议
        if risk_level in ["HIGH", "MEDIUM_HIGH"]:
            recommendations.append("风险等级较高，建议加强风险控制")
        elif risk_level == "LOW":
            recommendations.append("风险等级较低，可适度提高风险偏好")
        
        # 默认建议
        if not recommendations:
            recommendations.append("投资组合配置合理，建议保持当前策略")
        
        return recommendations
    
    async def monitor_market(self, market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        监控市场
        
        Args:
            market_conditions: 市场条件
            
        Returns:
            市场监控结果
        """
        logger.info("监控市场...")
        
        # 这里可以实现市场监控逻辑
        # 例如：监控关键指标、检测异常、生成警报等
        
        market_status = market_conditions.get("status", "NORMAL")
        volatility = market_conditions.get("volatility", 0.2)
        trend = market_conditions.get("trend", "NEUTRAL")
        
        # 生成监控报告
        monitoring_result = {
            "timestamp": datetime.now(),
            "market_status": market_status,
            "volatility": volatility,
            "trend": trend,
            "recommendations": []
        }
        
        # 根据市场状态生成建议
        if market_status == "VOLATILE" and volatility > 0.3:
            monitoring_result["recommendations"].append("市场波动较大，建议降低仓位")
        
        if trend == "BEARISH":
            monitoring_result["recommendations"].append("市场趋势偏空，建议谨慎操作")
        elif trend == "BULLISH":
            monitoring_result["recommendations"].append("市场趋势偏多，可适度积极")
        
        return monitoring_result