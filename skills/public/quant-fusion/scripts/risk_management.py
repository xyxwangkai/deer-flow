#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险管理模块
集成Qlib、AlphaCouncil、TradingAgents的风险管理功能
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """风险指标类"""
    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    cvar_95: float  # 95% CVaR
    cvar_99: float  # 99% CVaR
    volatility: float  # 波动率
    beta: float  # Beta系数
    sharpe_ratio: float  # 夏普比率
    max_drawdown: float  # 最大回撤
    sortino_ratio: float  # 索提诺比率
    calmar_ratio: float  # 卡玛比率
    information_ratio: float  # 信息比率
    tracking_error: float  # 跟踪误差


@dataclass
class RiskLimit:
    """风险限额类"""
    max_position_size: float  # 最大仓位规模
    max_daily_loss: float  # 最大日亏损
    max_concentration: float  # 最大集中度
    max_leverage: float  # 最大杠杆
    stop_loss: float  # 止损线
    var_limit: float  # VaR限额


@dataclass
class RiskAlert:
    """风险警报类"""
    alert_id: str
    level: str  # LOW, MEDIUM, HIGH, CRITICAL
    type: str  # POSITION, MARKET, LIQUIDITY, OPERATIONAL
    message: str
    symbol: Optional[str] = None
    metric: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False


class RiskManager:
    """风险管理器 - 集成三大项目的风控功能"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化风险管理器
        
        Args:
            config: 风险配置
        """
        self.config = config
        self.risk_limits = self._load_risk_limits()
        self.alerts = []
        self.historical_returns = {}
        self.correlation_matrix = {}
        
        # 初始化风险模型
        self.risk_models = self._init_risk_models()
        
        logger.info("风险管理器初始化完成")
    
    def _load_risk_limits(self) -> RiskLimit:
        """加载风险限额"""
        risk_config = self.config.get("risk_management", {})
        
        return RiskLimit(
            max_position_size=risk_config.get("max_position_size", 0.1),
            max_daily_loss=risk_config.get("max_daily_loss", 0.05),
            max_concentration=risk_config.get("max_concentration", 0.3),
            max_leverage=risk_config.get("max_leverage", 1.0),
            stop_loss=risk_config.get("stop_loss", 0.03),
            var_limit=risk_config.get("var_limit", 0.02)
        )
    
    def _init_risk_models(self) -> Dict[str, Any]:
        """初始化风险模型"""
        models = {}
        
        try:
            # VaR模型
            from risk_models.var_model import VaRModel
            models["var"] = VaRModel(self.config)
        except ImportError:
            logger.warning("VaR模型导入失败，使用模拟模型")
            models["var"] = self._create_mock_var_model()
        
        try:
            # 压力测试模型
            from risk_models.stress_test import StressTestModel
            models["stress"] = StressTestModel(self.config)
        except ImportError:
            logger.warning("压力测试模型导入失败，使用模拟模型")
            models["stress"] = self._create_mock_stress_model()
        
        try:
            # 流动性风险模型
            from risk_models.liquidity_risk import LiquidityRiskModel
            models["liquidity"] = LiquidityRiskModel(self.config)
        except ImportError:
            logger.warning("流动性风险模型导入失败，使用模拟模型")
            models["liquidity"] = self._create_mock_liquidity_model()
        
        try:
            # 信用风险模型
            from risk_models.credit_risk import CreditRiskModel
            models["credit"] = CreditRiskModel(self.config)
        except ImportError:
            logger.warning("信用风险模型导入失败，使用模拟模型")
            models["credit"] = self._create_mock_credit_model()
        
        return models
    
    def _create_mock_var_model(self):
        """创建模拟VaR模型"""
        class MockVaRModel:
            def __init__(self, config):
                self.config = config
            
            async def calculate(self, portfolio, market_data):
                return {
                    "var_95": 0.05,
                    "var_99": 0.08,
                    "cvar_95": 0.07,
                    "cvar_99": 0.10
                }
        
        return MockVaRModel(self.config)
    
    def _create_mock_stress_model(self):
        """创建模拟压力测试模型"""
        class MockStressTestModel:
            def __init__(self, config):
                self.config = config
            
            async def run_scenario(self, scenario_name):
                # 模拟压力测试结果
                scenarios = {
                    "market_crash": {"loss": -0.20, "description": "市场崩盘"},
                    "liquidity_crisis": {"loss": -0.15, "description": "流动性危机"},
                    "interest_rate_spike": {"loss": -0.10, "description": "利率飙升"},
                    "black_swan": {"loss": -0.30, "description": "黑天鹅事件"},
                    "mild_correction": {"loss": -0.05, "description": "温和回调"}
                }
                return scenarios.get(scenario_name, {"loss": -0.10, "description": "未知场景"})
        
        return MockStressTestModel(self.config)
    
    def _create_mock_liquidity_model(self):
        """创建模拟流动性风险模型"""
        class MockLiquidityRiskModel:
            def __init__(self, config):
                self.config = config
            
            async def assess(self, portfolio, market_data):
                return {
                    "liquidity_score": 0.8,
                    "estimated_slippage": 0.002,
                    "time_to_exit": 2.5
                }
        
        return MockLiquidityRiskModel(self.config)
    
    def _create_mock_credit_model(self):
        """创建模拟信用风险模型"""
        class MockCreditRiskModel:
            def __init__(self, config):
                self.config = config
            
            async def evaluate(self, portfolio, market_data):
                return {
                    "credit_score": 0.9,
                    "default_probability": 0.01,
                    "recovery_rate": 0.6
                }
        
        return MockCreditRiskModel(self.config)
    
    async def assess_portfolio_risk(self, portfolio: Dict[str, Any], 
                                  market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估投资组合风险
        
        Args:
            portfolio: 投资组合数据
            market_data: 市场数据
            
        Returns:
            风险评估结果
        """
        logger.info("开始投资组合风险评估")
        
        risk_assessment = {
            "timestamp": datetime.now().isoformat(),
            "portfolio_summary": {},
            "risk_metrics": {},
            "stress_tests": {},
            "alerts": [],
            "recommendations": []
        }
        
        try:
            # 1. 计算基础风险指标
            risk_metrics = await self._calculate_basic_risk_metrics(portfolio, market_data)
            risk_assessment["risk_metrics"] = risk_metrics
            
            # 2. 运行压力测试
            stress_results = await self._run_stress_tests(portfolio, market_data)
            risk_assessment["stress_tests"] = stress_results
            
            # 3. 检查风险限额
            limit_checks = await self._check_risk_limits(portfolio, market_data)
            risk_assessment["alerts"].extend(limit_checks)
            
            # 4. 计算VaR
            var_results = await self._calculate_var(portfolio, market_data)
            risk_assessment["var_analysis"] = var_results
            
            # 5. 生成风险报告
            report = await self._generate_risk_report(
                risk_metrics, stress_results, limit_checks, var_results
            )
            risk_assessment["risk_report"] = report
            
            # 6. 生成建议
            recommendations = await self._generate_risk_recommendations(
                risk_metrics, limit_checks
            )
            risk_assessment["recommendations"] = recommendations
            
            logger.info("投资组合风险评估完成")
            
        except Exception as e:
            logger.error(f"风险评估失败: {e}")
            risk_assessment["error"] = str(e)
        
        return risk_assessment
    
    async def _calculate_basic_risk_metrics(self, portfolio: Dict[str, Any],
                                          market_data: Dict[str, Any]) -> RiskMetrics:
        """计算基础风险指标"""
        # 提取投资组合收益数据
        returns = self._extract_portfolio_returns(portfolio, market_data)
        
        if len(returns) < 10:
            logger.warning("收益数据不足，使用默认值")
            return self._get_default_risk_metrics()
        
        # 计算波动率
        volatility = np.std(returns) * np.sqrt(252)  # 年化波动率
        
        # 计算VaR和CVaR
        var_95, var_99, cvar_95, cvar_99 = self._calculate_var_cvar(returns)
        
        # 计算Beta (简化版)
        beta = self._calculate_beta(returns, market_data)
        
        # 计算夏普比率
        risk_free_rate = 0.02  # 假设无风险利率2%
        excess_returns = returns - risk_free_rate / 252
        sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        
        # 计算最大回撤
        cumulative_returns = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = np.min(drawdown)
        
        # 计算索提诺比率
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        sortino_ratio = np.mean(excess_returns) / downside_std * np.sqrt(252) if downside_std > 0 else 0
        
        # 计算卡玛比率
        calmar_ratio = np.mean(returns) * 252 / abs(max_drawdown) if max_drawdown != 0 else 0
        
        return RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            volatility=volatility,
            beta=beta,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            information_ratio=0,  # 需要基准数据
            tracking_error=0      # 需要基准数据
        )
    
    def _extract_portfolio_returns(self, portfolio: Dict[str, Any],
                                 market_data: Dict[str, Any]) -> np.ndarray:
        """提取投资组合收益数据"""
        returns = []
        
        # 这里应该从历史数据中提取实际收益
        # 目前生成模拟收益
        
        if "historical_returns" in portfolio:
            returns = portfolio["historical_returns"]
        else:
            # 生成模拟收益数据
            days = 252  # 一年交易日
            returns = np.random.normal(0.0005, 0.015, days)  # 日均收益0.05%，波动1.5%
        
        return np.array(returns)
    
    def _calculate_var_cvar(self, returns: np.ndarray) -> Tuple[float, float, float, float]:
        """计算VaR和CVaR"""
        if len(returns) == 0:
            return 0, 0, 0, 0
        
        # 95% VaR和CVaR
        var_95 = np.percentile(returns, 5)
        cvar_95 = returns[returns <= var_95].mean() if np.any(returns <= var_95) else var_95
        
        # 99% VaR和CVaR
        var_99 = np.percentile(returns, 1)
        cvar_99 = returns[returns <= var_99].mean() if np.any(returns <= var_99) else var_99
        
        return var_95, var_99, cvar_95, cvar_99
    
    def _calculate_beta(self, portfolio_returns: np.ndarray,
                       market_data: Dict[str, Any]) -> float:
        """计算Beta系数"""
        # 这里应该使用市场基准收益计算Beta
        # 目前返回模拟值
        
        if "market_returns" in market_data:
            market_returns = market_data["market_returns"]
            if len(market_returns) == len(portfolio_returns):
                covariance = np.cov(portfolio_returns, market_returns)[0, 1]
                market_variance = np.var(market_returns)
                beta = covariance / market_variance if market_variance > 0 else 1.0
                return beta
        
        # 返回模拟Beta
        return np.random.uniform(0.8, 1.2)
    
    def _get_default_risk_metrics(self) -> RiskMetrics:
        """获取默认风险指标"""
        return RiskMetrics(
            var_95=-0.02,
            var_99=-0.03,
            cvar_95=-0.025,
            cvar_99=-0.035,
            volatility=0.2,
            beta=1.0,
            sharpe_ratio=0.5,
            max_drawdown=-0.15,
            sortino_ratio=0.6,
            calmar_ratio=0.3,
            information_ratio=0,
            tracking_error=0
        )
    
    async def _run_stress_tests(self, portfolio: Dict[str, Any],
                              market_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行压力测试"""
        logger.info("运行压力测试")
        
        stress_scenarios = [
            {"name": "市场崩盘", "market_change": -0.20, "volatility_change": 2.0},
            {"name": "流动性危机", "market_change": -0.15, "liquidity_drop": 0.5},
            {"name": "利率飙升", "market_change": -0.10, "rate_increase": 0.03},
            {"name": "黑天鹅事件", "market_change": -0.30, "volatility_change": 3.0},
            {"name": "温和回调", "market_change": -0.05, "volatility_change": 1.5}
        ]
        
        results = {}
        
        for scenario in stress_scenarios:
            try:
                scenario_result = await self.risk_models["stress"].run_scenario(
                    portfolio, market_data, scenario
                )
                results[scenario["name"]] = scenario_result
            except Exception as e:
                logger.error(f"压力测试失败 {scenario['name']}: {e}")
                results[scenario["name"]] = {"error": str(e)}
        
        return results
    
    async def _check_risk_limits(self, portfolio: Dict[str, Any],
                               market_data: Dict[str, Any]) -> List[RiskAlert]:
        """检查风险限额"""
        alerts = []
        
        # 检查仓位规模
        if "positions" in portfolio:
            total_value = sum(pos.get("value", 0) for pos in portfolio["positions"])
            capital = portfolio.get("capital", 1)
            position_ratio = total_value / capital if capital > 0 else 0
            
            if position_ratio > self.risk_limits.max_position_size:
                alert = RiskAlert(
                    alert_id=f"ALERT_{len(alerts)}",
                    level="HIGH",
                    type="POSITION",
                    message=f"仓位规模超过限额: {position_ratio:.1%} > {self.risk_limits.max_position_size:.1%}",
                    metric=position_ratio,
                    threshold=self.risk_limits.max_position_size
                )
                alerts.append(alert)
        
        # 检查集中度
        if "positions" in portfolio:
            for position in portfolio["positions"]:
                symbol = position.get("symbol", "UNKNOWN")
                position_value = position.get("value", 0)
                concentration = position_value / total_value if total_value > 0 else 0
                
                if concentration > self.risk_limits.max_concentration:
                    alert = RiskAlert(
                        alert_id=f"ALERT_{len(alerts)}",
                        level="MEDIUM",
                        type="POSITION",
                        message=f"{symbol} 集中度过高: {concentration:.1%} > {self.risk_limits.max_concentration:.1%}",
                        symbol=symbol,
                        metric=concentration,
                        threshold=self.risk_limits.max_concentration
                    )
                    alerts.append(alert)
        
        # 检查VaR限额
        if "risk_metrics" in portfolio:
            var_95 = portfolio["risk_metrics"].get("var_95", 0)
            if abs(var_95) > self.risk_limits.var_limit:
                alert = RiskAlert(
                    alert_id=f"ALERT_{len(alerts)}",
                    level="HIGH",
                    type="MARKET",
                    message=f"VaR超过限额: {abs(var_95):.1%} > {self.risk_limits.var_limit:.1%}",
                    metric=abs(var_95),
                    threshold=self.risk_limits.var_limit
                )
                alerts.append(alert)
        
        # 检查止损线
        if "current_pnl" in portfolio:
            pnl_ratio = portfolio["current_pnl"] / portfolio.get("capital", 1)
            if pnl_ratio < -self.risk_limits.stop_loss:
                alert = RiskAlert(
                    alert_id=f"ALERT_{len(alerts)}",
                    level="CRITICAL",
                    type="MARKET",
                    message=f"触及止损线: 亏损 {abs(pnl_ratio):.1%} > {self.risk_limits.stop_loss:.1%}",
                    metric=pnl_ratio,
                    threshold=-self.risk_limits.stop_loss
                )
                alerts.append(alert)
        
        return alerts
    
    async def _calculate_var(self, portfolio: Dict[str, Any],
                           market_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算风险价值"""
        try:
            var_results = await self.risk_models["var"].calculate(
                portfolio, market_data
            )
            return var_results
        except Exception as e:
            logger.error(f"VaR计算失败: {e}")
            return {"error": str(e)}
    
    async def _generate_risk_report(self, risk_metrics: RiskMetrics,
                                  stress_tests: Dict[str, Any],
                                  alerts: List[RiskAlert],
                                  var_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成风险报告"""
        report = {
            "executive_summary": {
                "overall_risk_level": self._determine_risk_level(risk_metrics, alerts),
                "key_risks": [alert.message for alert in alerts if alert.level in ["HIGH", "CRITICAL"]],
                "recommended_actions": []
            },
            "detailed_analysis": {
                "risk_metrics": {
                    "volatility": f"{risk_metrics.volatility:.1%}",
                    "var_95": f"{risk_metrics.var_95:.1%}",
                    "cvar_95": f"{risk_metrics.cvar_95:.1%}",
                    "max_drawdown": f"{risk_metrics.max_drawdown:.1%}",
                    "sharpe_ratio": f"{risk_metrics.sharpe_ratio:.2f}",
                    "beta": f"{risk_metrics.beta:.2f}"
                },
                "stress_test_results": {
                    scenario: {
                        "estimated_loss": result.get("estimated_loss", "N/A"),
                        "survival_probability": result.get("survival_probability", "N/A")
                    }
                    for scenario, result in stress_tests.items()
                },
                "var_analysis": var_analysis
            },
            "alerts_summary": {
                "total_alerts": len(alerts),
                "critical_alerts": len([a for a in alerts if a.level == "CRITICAL"]),
                "high_alerts": len([a for a in alerts if a.level == "HIGH"]),
                "medium_alerts": len([a for a in alerts if a.level == "MEDIUM"]),
                "low_alerts": len([a for a in alerts if a.level == "LOW"])
            }
        }
        
        return report
    
    def _determine_risk_level(self, risk_metrics: RiskMetrics,
                            alerts: List[RiskAlert]) -> str:
        """确定风险等级"""
        critical_count = len([a for a in alerts if a.level == "CRITICAL"])
        high_count = len([a for a in alerts if a.level == "HIGH"])
        
        if critical_count > 0:
            return "CRITICAL"
        elif high_count > 2:
            return "HIGH"
        elif risk_metrics.max_drawdown < -0.2:
            return "HIGH"
        elif high_count > 0 or risk_metrics.max_drawdown < -0.1:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def _generate_risk_recommendations(self, risk_metrics: RiskMetrics,
                                           alerts: List[RiskAlert]) -> List[str]:
        """生成风险建议"""
        recommendations = []
        
        # 基于风险指标的建议
        if risk_metrics.volatility > 0.3:
            recommendations.append("波动率过高，建议降低仓位或增加对冲")
        
        if risk_metrics.max_drawdown < -0.15:
            recommendations.append("回撤过大，建议设置更严格的止损")
        
        if risk_metrics.sharpe_ratio < 0:
            recommendations.append("夏普比率为负，投资组合表现不佳")
        
        # 基于警报的建议
        for alert in alerts:
            if alert.level in ["HIGH", "CRITICAL"]:
                if alert.type == "POSITION":
                    recommendations.append(f"降低 {alert.symbol or '相关'} 的仓位")
                elif alert.type == "MARKET":
                    recommendations.append("考虑增加对冲或降低风险敞口")
        
        # 通用建议
        if not recommendations:
            recommendations.append("风险状况良好，保持当前策略")
        
        return recommendations
    
    async def monitor_real_time_risk(self, portfolio: Dict[str, Any],
                                   market_data: Dict[str, Any]) -> List[RiskAlert]:
        """
        实时风险监控
        
        Args:
            portfolio: 投资组合数据
            market_data: 实时市场数据
            
        Returns:
            实时风险警报
        """
        alerts = []
        
        # 监控市场波动
        if "volatility" in market_data:
            current_vol = market_data["volatility"]
            if current_vol > 0.4:  # 波动率超过40%
                alert = RiskAlert(
                    alert_id=f"RT_ALERT_{len(alerts)}",
                    level="HIGH",
                    type="MARKET",
                    message=f"市场波动率异常升高: {current_vol:.1%}",
                    metric=current_vol
                )
                alerts.append(alert)
        
        # 监控流动性
        if "liquidity" in market_data:
            liquidity = market_data["liquidity"]
            if liquidity < 0.3:  # 流动性低于30%
                alert = RiskAlert(
                    alert_id=f"RT_ALERT_{len(alerts)}",
                    level="MEDIUM",
                    type="LIQUIDITY",
                    message=f"市场流动性下降: {liquidity:.1%}",
                    metric=liquidity
                )
                alerts.append(alert)
        
        # 监控投资组合实时盈亏
        if "real_time_pnl" in portfolio:
            pnl = portfolio["real_time_pnl"]
            capital = portfolio.get("capital", 1)
            pnl_ratio = pnl / capital
            
            if pnl_ratio < -0.02:  # 实时亏损超过2%
                alert = RiskAlert(
                    alert_id=f"RT_ALERT_{len(alerts)}",
                    level="MEDIUM",
                    type="MARKET",
                    message=f"实时亏损: {pnl_ratio:.1%}",
                    metric=pnl_ratio
                )
                alerts.append(alert)
        
        return alerts
    
    async def get_risk_dashboard(self) -> Dict[str, Any]:
        """获取风险仪表盘数据"""
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "active_alerts": len([a for a in self.alerts if not a.acknowledged]),
            "risk_level": "MEDIUM",  # 需要实时计算
            "key_metrics": {
                "var_95": -0.02,
                "volatility": 0.18,
                "max_drawdown": -0.12,
                "sharpe_ratio": 0.65
            },
            "recent_alerts": [
                {
                    "id": alert.alert_id,
                    "level": alert.level,
                    "message": alert.message,
                    "time": alert.timestamp.strftime("%H:%M:%S")
                }
                for alert in self.alerts[-5:]  # 最近5个警报
            ]
        }
        
        return dashboard